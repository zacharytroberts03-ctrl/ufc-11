"""Read/write the lessons.json store and regenerate the human-readable
lessons.md mirror. Pure Python, no LLM.

The lessons corpus has three buckets:
- lessons[]   active, high-confidence — injected into specialist prompts
- watchlist[] candidate patterns — observed but not yet trusted
- archived[]  inactive — kept for audit, not injected

Confidence promotion / archival rules are enforced by the merge-pass LLM,
not by this module. This module just reads, writes, and renders.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def empty_store() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "last_updated": None,
        "lessons": [],
        "watchlist": [],
        "archived": [],
    }


def load_lessons(path: str | Path) -> dict[str, Any]:
    """Load lessons.json. Returns empty_store() on missing file or parse error."""
    p = Path(path)
    if not p.exists():
        return empty_store()
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            return empty_store()
        return data
    except (json.JSONDecodeError, OSError):
        return empty_store()


def save_lessons(path: str | Path, store: dict[str, Any]) -> None:
    """Atomically write lessons.json (write to tmp then rename)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False, default=str)
    tmp.replace(p)


def lessons_for_agent(
    store: dict[str, Any],
    agent_name: str,
    max_lessons: int = 5,
) -> list[dict[str, Any]]:
    """Filter active high-confidence lessons that apply to a given agent.
    Sort by last_confirmed desc; cap at max_lessons."""
    candidates = [
        lesson for lesson in store.get("lessons", [])
        if lesson.get("confidence") == "high"
        and agent_name in lesson.get("applies_to", [])
    ]
    candidates.sort(key=lambda l: l.get("last_confirmed", ""), reverse=True)
    return candidates[:max_lessons]


def regenerate_markdown(store: dict[str, Any]) -> str:
    """Render lessons.json as a sorted, human-readable markdown document."""
    lines = []
    lines.append(f"# Lessons learned (auto-regenerated {store.get('last_updated', 'never')})")
    lines.append("")
    lines.append("This file is regenerated from `lessons.json` on every reflection run.")
    lines.append("Do not edit by hand — the merge pass will overwrite changes.")
    lines.append("")

    # Group active lessons by agent
    by_agent: dict[str, list[dict]] = {}
    for lesson in store.get("lessons", []):
        for agent in lesson.get("applies_to", []):
            by_agent.setdefault(agent, []).append(lesson)

    for agent in sorted(by_agent):
        lines.append(f"## {agent}")
        lines.append("")
        # Within an agent, sort by confidence then recency
        agent_lessons = sorted(
            by_agent[agent],
            key=lambda l: (l.get("confidence", ""), l.get("last_confirmed", "")),
            reverse=True,
        )
        for lesson in agent_lessons:
            conf = lesson.get("confidence", "?").upper()
            lid = lesson.get("id", "?")
            pattern = lesson.get("pattern", "?")
            correction = lesson.get("suggested_correction", "?")
            n = lesson.get("evidence_count", 0)
            since = lesson.get("first_seen", "?")
            last = lesson.get("last_confirmed", "?")
            lines.append(f"### [{conf}] {lid}")
            lines.append(f"**Pattern:** {pattern}")
            lines.append(f"**Correction:** {correction}")
            lines.append(f"**Evidence:** {n} observations since {since}")
            lines.append(f"**Last confirmed:** {last}")
            lines.append("")

    # Watchlist
    watchlist = store.get("watchlist", [])
    if watchlist:
        lines.append("---")
        lines.append("")
        lines.append("## Watchlist (not yet injected)")
        lines.append("")
        for w in watchlist:
            lines.append(f"- **{w.get('id', '?')}** ({', '.join(w.get('applies_to', []))})"
                         f" — {w.get('pattern', '?')}"
                         f" ({w.get('evidence_count', 0)} obs)")
        lines.append("")

    # Archived count only (don't dump full archived entries to the markdown view)
    archived = store.get("archived", [])
    if archived:
        lines.append("---")
        lines.append(f"_{len(archived)} archived lessons (see lessons.json)_")

    return "\n".join(lines) + "\n"


def save_markdown(path: str | Path, store: dict[str, Any]) -> None:
    """Write the regenerated markdown view to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(regenerate_markdown(store), encoding="utf-8")
