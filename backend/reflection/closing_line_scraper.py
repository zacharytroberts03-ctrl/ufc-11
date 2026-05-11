"""Scrape closing moneylines for every fight on a completed UFC card from
BestFightOdds. Per fight, returns the most recent line we can find (treating
it as the closing line since the event is already over)."""

from __future__ import annotations

import sys
import os
import time

# Reuse the existing single-fight BFO scraper
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(BACKEND_DIR, "tools"))
from scrape_bestfightodds import scrape_line_movement  # noqa: E402


def _moneyline_to_implied_prob(ml: int) -> float:
    """Convert American moneyline to implied probability."""
    if ml < 0:
        return -ml / (-ml + 100)
    return 100 / (ml + 100)


def scrape_card_closing_lines(fights: list[dict], delay_sec: float = 1.0) -> dict:
    """Args:
        fights: list of dicts each with at least {fighter1, fighter2}.

    Returns:
        {
            fight_key: {
                "f1_moneyline": int | None,
                "f1_implied_prob": float | None,
                "source": "bestfightodds",
                "scraped_at": iso8601 str,
            },
            ...
        }
    fight_key is "<f1>__<f2>" (slug-style). Entries with no data have None values.
    """
    import datetime as _dt
    out = {}
    for f in fights:
        f1, f2 = f["fighter1"], f["fighter2"]
        key = f"{f1}__{f2}"
        lm = None
        try:
            lm = scrape_line_movement(f1, f2)
        except Exception as e:
            print(f"  closing line scrape failed for {f1} vs {f2}: {e!r}", file=sys.stderr)
        time.sleep(delay_sec)

        if not lm or f1 not in lm:
            out[key] = {
                "f1_moneyline": None,
                "f1_implied_prob": None,
                "source": "bestfightodds",
                "scraped_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            }
            continue

        # Treat 'current' as closing line (event is already over)
        f1_ml = lm[f1].get("current")
        out[key] = {
            "f1_moneyline": f1_ml,
            "f1_implied_prob": _moneyline_to_implied_prob(f1_ml) if f1_ml is not None else None,
            "source": "bestfightodds",
            "scraped_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }
    return out
