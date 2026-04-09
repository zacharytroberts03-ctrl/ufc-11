"""Persistent JSON cache for pre-generated fight analyses."""

import json
import os
import re

BASE_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "analyses.json")


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unknown"


def fight_key(f1: str, f2: str) -> str:
    """Order-independent key for a fight."""
    a, b = sorted([_slug(f1), _slug(f2)])
    return f"{a}__{b}"


def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {"event_key": None, "generated_at": None, "fights": {}}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "fights" not in data:
            data["fights"] = {}
        return data
    except (json.JSONDecodeError, OSError):
        return {"event_key": None, "generated_at": None, "fights": {}}


def save_cache(cache: dict) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, default=str)


def get_cached_analysis(f1: str, f2: str) -> dict | None:
    cache = load_cache()
    return cache.get("fights", {}).get(fight_key(f1, f2))
