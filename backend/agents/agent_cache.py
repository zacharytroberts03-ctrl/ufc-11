"""On-disk cache for specialist agent reports.

Cache key: (fighter_slug, agent_name, opponent_slug_or_solo, last_fight_date)
A fighter's reports stay valid until they have a new fight (last_fight_date
changes). Opponent dimension matters because matchup_notes_vs_opponent differs
per matchup; this cache stores the full report keyed by all four dimensions
for simplicity. Future optimization: split opponent-agnostic fields out and
re-derive only matchup_notes per opponent.

Stored at backend/cache/agent_reports.json."""

from __future__ import annotations

import json
import os
import re
import threading

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CACHE_DIR = os.path.join(BACKEND_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "agent_reports.json")

_lock = threading.Lock()


def _slug(name: str | None) -> str:
    if not name:
        return "_solo"
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unknown"


def _key(fighter: str, agent: str, opponent: str | None, last_fight_date: str | None) -> str:
    return f"{_slug(fighter)}__{agent}__{_slug(opponent)}__{last_fight_date or 'no-date'}"


class AgentReportCache:
    def __init__(self, path: str = CACHE_FILE):
        self.path = path
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def get(self, fighter: str, agent: str, opponent: str | None, last_fight_date: str | None) -> dict | None:
        return self._data.get(_key(fighter, agent, opponent, last_fight_date))

    def put(self, fighter: str, agent: str, opponent: str | None, last_fight_date: str | None, parsed: dict) -> None:
        with _lock:
            self._data[_key(fighter, agent, opponent, last_fight_date)] = parsed

    def save(self) -> None:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with _lock:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, default=str)

    def stats(self) -> dict:
        return {"entries": len(self._data), "path": self.path}
