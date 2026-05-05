"""One-off: re-scrape Tapology intangibles for every fighter on the current
card and merge into frontend/public/data/analyses.json.

No Claude API calls — only Tapology HTTP scrapes. Use to backfill the new
nationality + fights_out_of fields without re-running the full agent pipeline.

Run from backend/:  python scripts/refresh_intangibles.py
"""

import json
import os
import sys
import time

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))
sys.path.insert(0, os.path.join(BACKEND_DIR, "tools"))

from scrape_tapology import scrape_tapology_intangibles
sys.path.insert(0, BACKEND_DIR)
from agents.fighter_overrides import apply_intangibles_overrides

ANALYSES_PATH = os.path.join(PROJECT_DIR, "frontend", "public", "data", "analyses.json")


def main() -> int:
    with open(ANALYSES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    fights = data.get("fights", {})
    if not fights:
        print("No fights in analyses.json", file=sys.stderr)
        return 1

    seen_names: set[str] = set()
    cache: dict[str, dict] = {}

    total = sum(2 for _ in fights)  # 2 fighters per fight
    i = 0
    for key, fight in fights.items():
        for side in ("f1_data", "f2_data"):
            i += 1
            fdata = fight.get(side) or {}
            name = fdata.get("name")
            if not name:
                print(f"  [{i}/{total}] {key} {side}: no name, skipping")
                continue

            if name in cache:
                fresh = cache[name]
            else:
                print(f"  [{i}/{total}] scraping {name}...", flush=True)
                fresh = scrape_tapology_intangibles(name) or {}
                cache[name] = fresh
                seen_names.add(name)
                time.sleep(0.5)  # be polite to Tapology

            existing = fdata.get("intangibles") or {}
            merged = dict(existing)
            for k, v in fresh.items():
                if v is not None:
                    merged[k] = v
            # Manual overrides for fields the scraper can't fill (e.g., Tapology
            # has empty Affiliation for some fighters).
            fdata["intangibles"] = apply_intangibles_overrides(name, merged)
            fight[side] = fdata

    with open(ANALYSES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\nDone — refreshed intangibles for {len(seen_names)} unique fighters")
    print(f"Wrote {ANALYSES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
