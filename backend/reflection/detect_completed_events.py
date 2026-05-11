"""Find UFC events that completed in the past N days AND that we have
predictions for in backend/cache/analyses.json."""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR / "tools"))
from scrape_ufc_card import _parse_event_list, _get  # noqa: E402

ANALYSES_CACHE = BACKEND_DIR / "cache" / "analyses.json"
LOOKBACK_DAYS = 7  # any event we predicted on in the past week is fair game


def _load_predicted_event_keys() -> set[str]:
    """Return the set of event_keys we have predictions for."""
    if not ANALYSES_CACHE.exists():
        return set()
    try:
        with ANALYSES_CACHE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return set()
    ek = data.get("event_key")
    return {ek} if ek else set()


def find_events_to_reflect_on(lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    """Returns events that:
       - completed in the past lookback_days
       - we have prediction cache for (event_key matches)

    Each returned item is {event_key, event_name, event_date, event_url}.
    """
    predicted_keys = _load_predicted_event_keys()
    if not predicted_keys:
        return []

    today = datetime.date.today()
    completed_html = _get("http://www.ufcstats.com/statistics/events/completed")
    completed = _parse_event_list(completed_html)

    out = []
    for ev in completed:
        if not ev.get("date"):
            continue
        days_ago = (today - ev["date"]).days
        if days_ago < 0 or days_ago > lookback_days:
            continue
        # Build event_key the same way refresh_cache.py does
        slug = "".join(c.lower() if c.isalnum() else "-" for c in ev["name"]).strip("-")
        ek = f"{slug}__{ev['date_str']}"
        if ek in predicted_keys:
            out.append({
                "event_key": ek,
                "event_name": ev["name"],
                "event_date": ev["date_str"],
                "event_url": ev["url"],
            })
    return out


if __name__ == "__main__":
    events = find_events_to_reflect_on()
    print(json.dumps(events, indent=2))
