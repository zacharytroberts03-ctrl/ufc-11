"""Unit tests for backend.reflection.lesson_store."""

import json
import pytest
from pathlib import Path
from backend.reflection.lesson_store import (
    load_lessons,
    save_lessons,
    regenerate_markdown,
    lessons_for_agent,
    empty_store,
)


def test_empty_store_shape():
    s = empty_store()
    assert s["schema_version"] == 1
    assert s["lessons"] == []
    assert s["watchlist"] == []
    assert s["archived"] == []


def test_load_lessons_missing_file_returns_empty(tmp_path):
    p = tmp_path / "lessons.json"
    s = load_lessons(p)
    assert s == empty_store()


def test_save_then_load_roundtrip(tmp_path):
    p = tmp_path / "lessons.json"
    store = empty_store()
    store["lessons"].append({
        "id": "lesson_001",
        "applies_to": ["ufc-striking-offense"],
        "pattern": "Test pattern",
        "confidence": "high",
        "status": "active",
        "evidence_count": 3,
        "first_seen": "2026-03-01",
        "last_confirmed": "2026-05-11",
        "examples": [],
        "suggested_correction": "Test correction",
    })
    save_lessons(p, store)
    loaded = load_lessons(p)
    assert loaded == store


def test_load_lessons_corrupted_returns_empty(tmp_path):
    p = tmp_path / "lessons.json"
    p.write_text("{not valid json", encoding="utf-8")
    s = load_lessons(p)
    assert s == empty_store()


def test_lessons_for_agent_filters_by_applies_to_and_confidence():
    store = empty_store()
    store["lessons"] = [
        {"id": "L1", "applies_to": ["ufc-striking-offense"], "confidence": "high",
         "pattern": "P1", "suggested_correction": "C1", "evidence_count": 4,
         "first_seen": "2026-03-01", "last_confirmed": "2026-05-11"},
        {"id": "L2", "applies_to": ["ufc-grappling-offense"], "confidence": "high",
         "pattern": "P2", "suggested_correction": "C2", "evidence_count": 3,
         "first_seen": "2026-03-01", "last_confirmed": "2026-05-11"},
        {"id": "L3", "applies_to": ["ufc-striking-offense"], "confidence": "medium",
         "pattern": "P3", "suggested_correction": "C3", "evidence_count": 2,
         "first_seen": "2026-03-01", "last_confirmed": "2026-05-11"},
    ]
    result = lessons_for_agent(store, "ufc-striking-offense", max_lessons=5)
    assert len(result) == 1
    assert result[0]["id"] == "L1"


def test_lessons_for_agent_caps_at_max():
    store = empty_store()
    store["lessons"] = [
        {"id": f"L{i}", "applies_to": ["ufc-striking-offense"], "confidence": "high",
         "pattern": f"P{i}", "suggested_correction": f"C{i}", "evidence_count": 4,
         "first_seen": "2026-03-01", "last_confirmed": f"2026-05-{10 - i:02d}"}
        for i in range(10)
    ]
    result = lessons_for_agent(store, "ufc-striking-offense", max_lessons=5)
    assert len(result) == 5
    # Most recent (highest last_confirmed) first
    assert result[0]["id"] == "L0"


def test_regenerate_markdown_groups_by_agent(tmp_path):
    store = empty_store()
    store["lessons"] = [
        {"id": "L1", "applies_to": ["ufc-striking-offense"], "confidence": "high",
         "pattern": "Over-rate counter-strikers", "suggested_correction": "Cap at 7",
         "evidence_count": 3, "first_seen": "2026-03-01", "last_confirmed": "2026-05-11",
         "examples": []},
    ]
    md = regenerate_markdown(store)
    assert "## ufc-striking-offense" in md
    assert "Over-rate counter-strikers" in md
    assert "[HIGH]" in md
    assert "3 observations" in md
