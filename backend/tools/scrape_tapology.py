"""
Tool: scrape_tapology.py
Purpose: Pull intangibles for a UFC fighter from tapology.com — specifically:
            • camp / gym affiliation
            • weight-miss history flag
            • (short-notice flag is left as None — Tapology does not expose it cleanly)

Used by analysis_runner to feed Section 9 (Intangibles).

Returns a dict shaped like:
    {
        "camp": "American Top Team",
        "weight_miss_history": "1 miss in last 12 months",
        "short_notice": None,
        "notice_days": None,
    }

If scraping fails, returns an empty dict {}. Never raises.

Usage:
    from scrape_tapology import scrape_tapology_intangibles
    info = scrape_tapology_intangibles("Jiri Prochazka")
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
BASE = "https://www.tapology.com"


def _get(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def _find_fighter_url(name: str) -> str | None:
    """Search Tapology for a fighter and return their profile URL, or None."""
    q = urllib.parse.quote(name)
    html = _get(f"{BASE}/search?term={q}&mainSearchFilter=fighters")
    if not html:
        return None
    m = re.search(r'href="(/fightcenter/fighters/[^"]+)"', html)
    if not m:
        return None
    return BASE + m.group(1)


def _parse_camp(html: str) -> str | None:
    """Look for 'Affiliation' or 'Gym' labels in the fighter info block."""
    for label in ("Affiliation", "Gym", "Team"):
        m = re.search(
            rf'>{label}\s*</[^>]+>\s*<[^>]+>([^<]+)<',
            html,
            re.IGNORECASE,
        )
        if m:
            val = m.group(1).strip()
            if val and val.lower() not in ("n/a", "--", "none"):
                return val
    return None


def _parse_weight_misses(html: str) -> str | None:
    """Look for 'Missed Weight' or 'MW' tags in the fight history table."""
    miss_count = len(re.findall(r'Missed Weight|missed weight|\bMW\b', html))
    if miss_count == 0:
        return None
    if miss_count == 1:
        return "1 weight miss in fight history"
    return f"{miss_count} weight misses in fight history"


def scrape_tapology_intangibles(name: str) -> dict:
    """
    Best-effort scrape of intangible signals from Tapology. Returns {} on failure.
    Caller is responsible for treating empty dict as "no data."
    """
    try:
        url = _find_fighter_url(name)
        if not url:
            return {}
        time.sleep(DELAY)

        html = _get(url)
        if not html:
            return {}

        return {
            "camp": _parse_camp(html),
            "weight_miss_history": _parse_weight_misses(html),
            "short_notice": None,   # not derivable from Tapology page alone
            "notice_days": None,
        }
    except Exception:
        return {}


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 2:
        print('Usage: python tools/scrape_tapology.py "Fighter Name"')
        sys.exit(1)
    result = scrape_tapology_intangibles(sys.argv[1])
    print(json.dumps(result, indent=2))
