"""Verify lesson injection into specialist + synthesizer system prompts."""

import json
import pytest
from pathlib import Path
from backend.reflection.lesson_store import save_lessons, empty_store


def _seed_lessons(tmp_path, lessons):
    p = tmp_path / "lessons.json"
    store = empty_store()
    store["lessons"] = lessons
    save_lessons(p, store)
    return p


def test_inject_lessons_appends_section_when_match(tmp_path, monkeypatch):
    """When a high-confidence lesson applies to the agent, the section appears."""
    from backend.agents import agent_runner
    monkeypatch.setattr(agent_runner, "_LESSONS_PATH", _seed_lessons(tmp_path, [
        {"id": "lesson_001", "applies_to": ["ufc-striking-offense"], "confidence": "high",
         "pattern": "Test pattern", "suggested_correction": "Test correction",
         "evidence_count": 4, "first_seen": "2026-03-01", "last_confirmed": "2026-05-11",
         "examples": []},
    ]))
    base = "You are a striking-offense analyst."
    result = agent_runner._inject_lessons(base, "ufc-striking-offense")
    assert "Field-tested adjustments" in result
    assert "Test pattern" in result
    assert "Test correction" in result


def test_inject_lessons_no_match_returns_base(tmp_path, monkeypatch):
    """No matching lesson -> system prompt unchanged."""
    from backend.agents import agent_runner
    monkeypatch.setattr(agent_runner, "_LESSONS_PATH", _seed_lessons(tmp_path, []))
    base = "You are a striking-offense analyst."
    result = agent_runner._inject_lessons(base, "ufc-striking-offense")
    assert result == base


def test_inject_lessons_filters_other_agents(tmp_path, monkeypatch):
    """Lessons for OTHER agents don't bleed in."""
    from backend.agents import agent_runner
    monkeypatch.setattr(agent_runner, "_LESSONS_PATH", _seed_lessons(tmp_path, [
        {"id": "lesson_002", "applies_to": ["ufc-grappling-offense"], "confidence": "high",
         "pattern": "Grappling pattern", "suggested_correction": "Grappling fix",
         "evidence_count": 4, "first_seen": "2026-03-01", "last_confirmed": "2026-05-11",
         "examples": []},
    ]))
    base = "Base prompt."
    result = agent_runner._inject_lessons(base, "ufc-striking-offense")
    assert result == base
    assert "Grappling pattern" not in result
