"""
Tool: scrape_bestfightodds.py
Purpose: Scrape line movement (opening line vs current best line) for a UFC
         matchup from bestfightodds.com. Used by analysis_runner to feed
         Section 10 (Market Edge Rules).

Returns a dict shaped like:
    {
        "<f1_name>": {"opening": -135, "current": -165, "direction": "shortened"},
        "<f2_name>": {"opening": +115, "current": +145, "direction": "lengthened"},
        "reverse_line_movement": False,
        "public_pct": {},   # not available from BFO; left empty in v1
    }

If anything fails, the entry-point function returns None and the caller is
expected to swallow it (analysis_runner already does). Never raises.

Usage:
    from scrape_bestfightodds import scrape_line_movement
    lm = scrape_line_movement("Jiri Prochazka", "Carlos Ulberg")
"""

import re
import time
import urllib.parse

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
TIMEOUT = 15
DELAY = 1
BASE = "https://www.bestfightodds.com"


def _get(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def _normalize_odds(text: str) -> int | None:
    """Parse a BFO odds cell ('-135', '+115', '−135') to int. Handles unicode minus."""
    if not text:
        return None
    cleaned = text.replace("−", "-").replace(",", "").strip()
    m = re.match(r'^([+-]?\d+)$', cleaned)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _find_fighter_url(name: str) -> str | None:
    """Search BFO for a fighter and return their profile URL, or None."""
    q = urllib.parse.quote(name)
    html = _get(f"{BASE}/search?query={q}")
    if not html:
        return None
    # First search result link to a fighter page
    m = re.search(r'href="(/fighters/[^"]+)"', html)
    if not m:
        return None
    return BASE + m.group(1)


def _extract_lines_from_fighter_page(html: str, opponent_name: str) -> dict | None:
    """
    Pull opening + current best lines for the named opponent from a fighter page.
    Returns {"f_open": int, "f_close": int, "opp_open": int, "opp_close": int} or None.
    """
    if not html:
        return None

    # Find the row block containing the opponent's name. BFO renders each
    # upcoming fight as a small table with two fighter rows.
    # Strategy: find the section starting with the opponent name and grab the
    # "Opening" and "Current Best" odds cells in its block.
    opp_lower = opponent_name.lower()

    # Strip tags and look for both names in proximity
    # Find a chunk of HTML that contains the opponent name
    name_pos = html.lower().find(opp_lower)
    if name_pos == -1:
        return None

    # Take a window around the name to find the matchup row
    start = max(0, name_pos - 4000)
    end = min(len(html), name_pos + 4000)
    chunk = html[start:end]

    # Look for the two odds cells closest to the opponent name.
    # BFO marks opening lines with class "op" and current best with "best-bet" or similar.
    # Defensive: any cell containing a sign+digit pattern.
    odds_cells = re.findall(r'>\s*([+-−]?\d{2,4})\s*<', chunk)
    odds_ints = [_normalize_odds(c) for c in odds_cells]
    odds_ints = [o for o in odds_ints if o is not None]

    if len(odds_ints) < 4:
        return None

    # Heuristic: first 2 are this-fighter open/current, next 2 are opponent open/current.
    # This is fragile and will need refinement once we see real BFO HTML.
    return {
        "f_open":   odds_ints[0],
        "f_close":  odds_ints[1],
        "opp_open": odds_ints[2],
        "opp_close": odds_ints[3],
    }


def _direction(open_odds: int, close_odds: int) -> str:
    """Describe how a line moved. 'shortened' = became more favored."""
    if open_odds == close_odds:
        return "flat"
    # Convert to implied prob to compare apples-to-apples
    def implied(o):
        return abs(o) / (abs(o) + 100) if o < 0 else 100 / (o + 100)
    delta = implied(close_odds) - implied(open_odds)
    if delta > 0.005:
        return "shortened"  # bettors moved this side toward favorite
    if delta < -0.005:
        return "lengthened"  # bettors moved this side toward dog
    return "flat"


def scrape_line_movement(f1_name: str, f2_name: str) -> dict | None:
    """
    Best-effort line movement scrape. Returns None on any failure.
    Caller (analysis_runner) is responsible for swallowing None.
    """
    url = _find_fighter_url(f1_name)
    if not url:
        return None
    time.sleep(DELAY)

    html = _get(url)
    if not html:
        return None

    parsed = _extract_lines_from_fighter_page(html, f2_name)
    if not parsed:
        return None

    f1_open, f1_close = parsed["f_open"], parsed["f_close"]
    f2_open, f2_close = parsed["opp_open"], parsed["opp_close"]

    return {
        f1_name: {
            "opening":   f1_open,
            "current":   f1_close,
            "direction": _direction(f1_open, f1_close),
        },
        f2_name: {
            "opening":   f2_open,
            "current":   f2_close,
            "direction": _direction(f2_open, f2_close),
        },
        # Reverse line movement requires public betting % data, which BFO
        # doesn't expose for free. Left as False until a public-% source is added.
        "reverse_line_movement": False,
        "public_pct": {},
    }


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 3:
        print('Usage: python tools/scrape_bestfightodds.py "Fighter 1" "Fighter 2"')
        sys.exit(1)
    result = scrape_line_movement(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2) if result else "No line movement data found.")
