#!/usr/bin/env python3
"""
refresh_cache.py — Pre-generate analyses for every fight on the current card.
Runs in GitHub Actions on a schedule; commits results to backend/cache/analyses.json.
"""
import json
import os
import re
import sys
import time

import requests

BACKEND = os.environ.get("BACKEND_URL", "https://backend-two-psi-85.vercel.app")
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "backend", "cache", "analyses.json")


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unknown"


def fight_key(f1: str, f2: str) -> str:
    a, b = sorted([_slug(f1), _slug(f2)])
    return f"{a}__{b}"


def main():
    print(f"Fetching card from {BACKEND}/api/card ...")
    try:
        card_resp = requests.get(f"{BACKEND}/api/card", timeout=30)
        card_resp.raise_for_status()
        card = card_resp.json()
    except Exception as e:
        print(f"ERROR: Could not fetch card: {e}")
        sys.exit(1)

    fights = card.get("main_card", []) + card.get("prelims", [])
    if not fights:
        print("No fights found on card — nothing to refresh.")
        sys.exit(0)

    print(f"Found {len(fights)} fights. Event: {card.get("event", "unknown")}")

    cache = {
        "event_key": f"{card.get("event", "unknown")}__{ card.get("date", "")} ".strip(),
        "generated_at": None,
        "fights": {},
    }

    for i, fight in enumerate(fights, 1):
        f1 = fight.get("fighter1") or fight.get("f1")
        f2 = fight.get("fighter2") or fight.get("f2")
        if not f1 or not f2:
            print(f"  [{i}/{len(fights)}] Skipping malformed fight entry: {fight}")
            continue

        print(f"  [{i}/{len(fights)}] Analyzing {f1} vs {f2} ...", flush=True)
        try:
            resp = requests.post(
                f"{BACKEND}/api/analyze",
                json={"f1": f1, "f2": f2},
                timeout=180,
            )
            resp.raise_for_status()
            result = resp.json()
            key = fight_key(f1, f2)
            cache["fights"][key] = result
            print(f"       Done.")
        except Exception as e:
            print(f"       FAILED: {e}")

        # Brief pause between calls to avoid hammering the backend
        if i < len(fights):
            time.sleep(3)

    out_path = os.path.abspath(OUT_FILE)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, default=str)

    print(f"Saved {len(cache["fights"])} analyses to {out_path}")


if __name__ == "__main__":
    main()
