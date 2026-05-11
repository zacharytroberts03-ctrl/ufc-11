"""Scrape actual fight outcomes for a completed UFC event from ufcstats.com.

Returns per-fight: winner name, method (KO/TKO | Submission | Decision | Other),
round (int or None for decisions), finish time, and basic post-fight stats
(significant strikes, takedowns, knockdowns, sub attempts).

Page layout (event-details/<id>) fight table columns (10 cells per row):
  0: Win/loss marker  — "win" text in green flag = fighter1 is the winner
  1: Fighter names    — two <a> tags stacked (winner listed first)
  2: Knockdowns       — two <p> stacked (f1, f2)
  3: Sig strikes      — two <p> stacked (f1, f2)
  4: Takedowns        — two <p> stacked (f1, f2)
  5: Sub attempts     — two <p> stacked (f1, f2)
  6: Weight class
  7: Method           — e.g. "S-DEC", "U-DEC", "KO/TKO Punches", "SUB Rear Naked Choke"
  8: Round            — numeric string; for decisions this is the last/final round
  9: Time             — "MM:SS"

Winner detection: cell 0 contains a green flag element whose text is "win" when
fighter1 (first listed in cell 1) won. On ufcstats the winner is always listed
first, so the "win" flag is the definitive signal; it is present on every
completed row.
"""

from __future__ import annotations

import re
import sys
import json
import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
TIMEOUT = 20

# Cell indices in the 10-column fight row
_COL_WIN_FLAG = 0
_COL_FIGHTERS = 1
_COL_KD       = 2
_COL_STR      = 3
_COL_TD       = 4
_COL_SUB      = 5
_COL_WEIGHT   = 6
_COL_METHOD   = 7
_COL_ROUND    = 8
_COL_TIME     = 9


def _get(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def _parse_method(raw: str) -> str:
    """Normalize a method cell string to a canonical label."""
    t = raw.upper()
    if "SUB" in t:
        return "Submission"
    if "KO" in t or "TKO" in t:
        return "KO/TKO"
    if "DEC" in t or "DECISION" in t:
        return "Decision"
    if "DQ" in t or "NC" in t:
        return "Other"
    # Fallback — treat anything else as Decision to avoid raising
    return "Decision"


def _parse_stacked_int(cell, idx: int) -> int:
    """Extract the (idx)-th <p> text as an integer; 0 on any error."""
    try:
        paragraphs = cell.find_all("p")
        if len(paragraphs) <= idx:
            return 0
        return int(paragraphs[idx].get_text(strip=True))
    except (ValueError, AttributeError):
        return 0


def scrape_event_results(event_url: str) -> dict:
    """Scrape per-fight outcomes from a completed event page.

    Returns::

        {
            "event_url": str,
            "fights": [
                {
                    "fighter1": str,
                    "fighter2": str,
                    "winner": str,            # one of the two fighters
                    "method": str,            # KO/TKO | Submission | Decision | Other
                    "round": int | None,      # None for decisions
                    "time": str,              # "MM:SS"
                    "stats": {
                        "sig_strikes_f1": int,
                        "sig_strikes_f2": int,
                        "takedowns_f1": int,
                        "takedowns_f2": int,
                        "knockdowns_f1": int,
                        "knockdowns_f2": int,
                        "sub_attempts_f1": int,
                        "sub_attempts_f2": int,
                    },
                },
                ...
            ],
        }
    """
    try:
        html = _get(event_url)
    except Exception as exc:
        log.error("outcome_scraper: failed to fetch %s — %s", event_url, exc)
        return {"event_url": event_url, "fights": []}

    soup = BeautifulSoup(html, "html.parser")

    # Every completed-fight row has class b-fight-details__table-row__hover
    rows = soup.find_all("tr", class_="b-fight-details__table-row__hover")
    log.debug("outcome_scraper: found %d fight rows", len(rows))

    fights: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for row_idx, row in enumerate(rows):
        try:
            cells = row.find_all("td")
            if len(cells) < 10:
                log.debug("outcome_scraper: row %d has only %d cells, skipping", row_idx, len(cells))
                continue

            # ── Fighters (cell 1) ────────────────────────────────────────────
            fighter_links = cells[_COL_FIGHTERS].find_all("a")
            if len(fighter_links) < 2:
                log.debug("outcome_scraper: row %d has < 2 fighter links, skipping", row_idx)
                continue

            fighter1 = re.sub(r"\s+", " ", fighter_links[0].get_text()).strip()
            fighter2 = re.sub(r"\s+", " ", fighter_links[1].get_text()).strip()

            if not fighter1 or not fighter2 or fighter1.lower() == fighter2.lower():
                continue

            key = (fighter1.lower(), fighter2.lower())
            if key in seen:
                continue
            seen.add(key)

            # ── Winner (cell 0) ──────────────────────────────────────────────
            # ufcstats always lists the winner first. The green "win" flag in
            # cell 0 confirms this; if the flag text is "win" the first fighter
            # won. The flag is present on every completed row, so we just read
            # the flag text for safety but rely on the ordering rule.
            flag_text = cells[_COL_WIN_FLAG].get_text(strip=True).lower()
            if "win" in flag_text:
                winner = fighter1  # winner listed first — definitive
            else:
                # Unexpected: no "win" flag. Fall back to fighter1 but log it.
                log.warning(
                    "outcome_scraper: row %d missing 'win' flag (got %r); defaulting winner to %s",
                    row_idx, flag_text, fighter1,
                )
                winner = fighter1

            # ── Method (cell 7) ─────────────────────────────────────────────
            method_raw = cells[_COL_METHOD].get_text(separator=" ", strip=True)
            method = _parse_method(method_raw)

            # ── Round (cell 8) ───────────────────────────────────────────────
            # For Decision bouts the page shows the last round (3 or 5). We
            # normalise to None per the schema contract.
            round_raw = cells[_COL_ROUND].get_text(strip=True)
            if method == "Decision":
                round_num: int | None = None
            else:
                try:
                    rn = int(round_raw)
                    round_num = rn if 1 <= rn <= 5 else None
                except ValueError:
                    round_num = None

            # ── Time (cell 9) ────────────────────────────────────────────────
            time_raw = cells[_COL_TIME].get_text(strip=True)
            time_str = time_raw if re.match(r"^\d+:\d{2}$", time_raw) else "0:00"

            # ── Stats (cells 2-5: KD, Str, TD, Sub) ─────────────────────────
            stats = {
                "knockdowns_f1":  _parse_stacked_int(cells[_COL_KD],  0),
                "knockdowns_f2":  _parse_stacked_int(cells[_COL_KD],  1),
                "sig_strikes_f1": _parse_stacked_int(cells[_COL_STR], 0),
                "sig_strikes_f2": _parse_stacked_int(cells[_COL_STR], 1),
                "takedowns_f1":   _parse_stacked_int(cells[_COL_TD],  0),
                "takedowns_f2":   _parse_stacked_int(cells[_COL_TD],  1),
                "sub_attempts_f1": _parse_stacked_int(cells[_COL_SUB], 0),
                "sub_attempts_f2": _parse_stacked_int(cells[_COL_SUB], 1),
            }

            fights.append({
                "fighter1": fighter1,
                "fighter2": fighter2,
                "winner":   winner,
                "method":   method,
                "round":    round_num,
                "time":     time_str,
                "stats":    stats,
            })

        except Exception as exc:  # noqa: BLE001
            log.error("outcome_scraper: error parsing row %d — %s", row_idx, exc, exc_info=True)
            # Never raise — skip the row and continue

    return {"event_url": event_url, "fights": fights}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    if len(sys.argv) < 2:
        print("Usage: python -m backend.reflection.outcome_scraper <event_url>", file=sys.stderr)
        sys.exit(1)

    result = scrape_event_results(sys.argv[1])
    print(json.dumps(result, indent=2))
