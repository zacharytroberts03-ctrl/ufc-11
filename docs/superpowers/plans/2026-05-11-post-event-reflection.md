# Post-Event Reflection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Sunday GHA workflow that scores each completed UFC event we predicted on, has Opus 4.7 reflect on the misses, and turns recurring patterns into per-agent prompt adjustments injected into the next refresh cycle.

**Architecture:** Two-layer reflection — pure-Python deterministic scoring (Brier, pick accuracy, line-beat ROI) emits `event_score.json`, then three Opus passes (per-fight findings → card meta → merge into `lessons.json`) curate a confidence-gated lesson corpus. `agent_runner.py` and `synthesizer.py` load `lessons.json` and append filtered high-confidence lessons to each call's system prompt.

**Tech Stack:** Python 3.12, pytest, requests + bs4 (scraping), anthropic SDK (Opus 4.7), GitHub Actions cron.

**Spec reference:** [docs/superpowers/specs/2026-05-11-post-event-reflection-design.md](../specs/2026-05-11-post-event-reflection-design.md)

---

## File structure

**Created:**
- `backend/reflection/__init__.py` — package marker
- `backend/reflection/__main__.py` — CLI entry: `python -m backend.reflection [--dry-run] [--event-key KEY]`
- `backend/reflection/detect_completed_events.py` — finds events to reflect on
- `backend/reflection/outcome_scraper.py` — scrapes UFCstats results
- `backend/reflection/closing_line_scraper.py` — scrapes BestFightOdds closing line per fight on a card
- `backend/reflection/score.py` — pure-Python deterministic scoring
- `backend/reflection/reflect_runner.py` — the three Opus passes
- `backend/reflection/lesson_store.py` — read/write lessons.json + regenerate lessons.md
- `backend/reflection/prompts/per_fight_reflection.md`
- `backend/reflection/prompts/card_meta_pass.md`
- `backend/reflection/prompts/lesson_merge.md`
- `backend/reflection/tests/__init__.py`
- `backend/reflection/tests/test_score.py`
- `backend/reflection/tests/test_lesson_store.py`
- `backend/reflection/tests/test_inject_lessons.py`
- `backend/cache/lessons.json` — seeded empty
- `.github/workflows/reflect.yml`

**Modified:**
- `backend/requirements.txt` — add `pytest`
- `backend/agents/agent_runner.py` — call `_inject_lessons` when building specialist payload
- `backend/agents/synthesizer.py` — call `_inject_lessons` when building synthesizer instructions
- `CLAUDE.md` — new "Reflection pipeline" section + don't-do entry

---

## Task 1: Bootstrap — package skeleton + pytest

**Files:**
- Create: `backend/reflection/__init__.py`
- Create: `backend/reflection/tests/__init__.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add pytest to requirements.txt**

Modify [backend/requirements.txt](../../../backend/requirements.txt) — append `pytest` on a new line:

```
fastapi
uvicorn[standard]
anthropic
firecrawl-py
python-dotenv
requests
beautifulsoup4
Pillow
python-multipart
pytest
```

- [ ] **Step 2: Install pytest locally**

Run from project root:

```bash
pip install pytest
```

Expected: `Successfully installed pytest-<version>`

- [ ] **Step 3: Create package skeletons**

Create `backend/__init__.py` as empty file if it does not already exist. This is required so `from backend.reflection.X import ...` resolves correctly from pytest and from the GHA workflow's working directory. (The existing scripts work via `sys.path` tricks rather than the package import path, so adding this empty `__init__.py` won't disturb them.)

Create `backend/reflection/__init__.py` with content:

```python
"""Post-event reflection package. Reads our predictions + actual outcomes,
computes deterministic scoring, then runs three Opus passes to turn recurring
prediction errors into a per-agent lessons corpus that injects into future
specialist prompts.

See docs/superpowers/specs/2026-05-11-post-event-reflection-design.md.
"""
```

Create `backend/reflection/tests/__init__.py` as empty file.

- [ ] **Step 4: Verify pytest discovers the package**

Run from project root:

```bash
pytest backend/reflection/tests/ -v --collect-only
```

Expected: `collected 0 items` (no tests yet, but no import errors).

- [ ] **Step 5: Commit**

```bash
git add backend/__init__.py backend/requirements.txt backend/reflection/__init__.py backend/reflection/tests/__init__.py
git commit -m "Bootstrap backend/reflection package with pytest"
```

(If `backend/__init__.py` already existed, drop it from the `git add` line — `git status` will tell you.)

---

## Task 2: Deterministic scoring (TDD)

**Files:**
- Create: `backend/reflection/score.py`
- Create: `backend/reflection/tests/test_score.py`

- [ ] **Step 1: Write failing tests for the public API**

Create `backend/reflection/tests/test_score.py`:

```python
"""Unit tests for backend.reflection.score — deterministic, no LLM."""

import pytest
from backend.reflection.score import score_fight, score_card


def _baseline_prediction():
    return {
        "winner": "Arnold Allen",
        "win_prob": 0.62,
        "method": {"ko_tko": 0.25, "submission": 0.05, "decision": 0.70},
        "rounds": {
            "ends_round_1": 0.05,
            "ends_round_2": 0.10,
            "ends_round_3": 0.10,
            "ends_round_4_or_later": 0.05,
            "goes_to_decision": 0.70,
        },
    }


def _baseline_actual(winner="Arnold Allen", method="Decision", round_=3):
    return {"winner": winner, "method": method, "round": round_, "time": "5:00"}


def _baseline_closing_line(f1_implied=0.677):
    return {"f1_moneyline": -210, "f1_implied_prob": f1_implied}


def test_pick_correct_when_winner_matches():
    s = score_fight(
        fighter1="Arnold Allen",
        fighter2="Melquizael Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(),
    )
    assert s["pick_correct"] is True


def test_pick_wrong_when_winner_loses():
    s = score_fight(
        fighter1="Arnold Allen",
        fighter2="Melquizael Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(winner="Melquizael Costa"),
        closing_line=_baseline_closing_line(),
    )
    assert s["pick_correct"] is False


def test_method_correct_decision_vs_decision():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),  # decision is highest at 0.70
        actual=_baseline_actual(method="Decision"),
        closing_line=_baseline_closing_line(),
    )
    assert s["method_correct"] is True


def test_method_wrong_when_predicted_decision_actual_ko():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(method="KO/TKO"),
        closing_line=_baseline_closing_line(),
    )
    assert s["method_correct"] is False


def test_round_correct_when_predicted_decision_actual_decision():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),  # goes_to_decision is 0.70
        actual=_baseline_actual(method="Decision"),
        closing_line=_baseline_closing_line(),
    )
    # Decision has no specific round; round_correct compares "decision predicted" vs "actual was decision"
    assert s["round_correct"] is True


def test_brier_score_for_correct_pick():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),  # win_prob 0.62 for Allen
        actual=_baseline_actual(winner="Arnold Allen"),
        closing_line=_baseline_closing_line(),
    )
    # Brier = (0.62 - 1.0)^2 = 0.1444
    assert s["brier_score"] == pytest.approx(0.1444, abs=1e-4)


def test_brier_score_for_wrong_pick():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(winner="Melquizael Costa"),
        closing_line=_baseline_closing_line(),
    )
    # Brier = (0.62 - 0.0)^2 = 0.3844
    assert s["brier_score"] == pytest.approx(0.3844, abs=1e-4)


def test_bet_signal_pass_when_we_agree_with_market():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "win_prob": 0.66},
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(f1_implied=0.68),  # |0.66-0.68|<=0.05
    )
    assert s["line_beat"]["bet_signal"] == "pass"


def test_bet_signal_back_f1_when_we_undervalue_market():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "win_prob": 0.80},
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(f1_implied=0.60),  # edge +0.20 → back_f1
    )
    assert s["line_beat"]["bet_signal"] == "back_f1"


def test_bet_signal_back_f2_when_market_overvalues_f1():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "winner": "Arnold Allen", "win_prob": 0.40},
        actual=_baseline_actual(),
        closing_line=_baseline_closing_line(f1_implied=0.70),  # edge -0.30 → back_f2
    )
    assert s["line_beat"]["bet_signal"] == "back_f2"


def test_line_beat_profitable_when_we_back_winner():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted={**_baseline_prediction(), "win_prob": 0.80},
        actual=_baseline_actual(winner="Arnold Allen"),
        closing_line=_baseline_closing_line(f1_implied=0.60),
    )
    assert s["line_beat"]["bet_signal"] == "back_f1"
    assert s["line_beat"]["would_have_been_profitable"] is True


def test_closing_line_null_yields_null_line_beat():
    s = score_fight(
        fighter1="Arnold Allen", fighter2="Costa",
        predicted=_baseline_prediction(),
        actual=_baseline_actual(),
        closing_line=None,
    )
    assert s["line_beat"] is None
    # Other metrics still compute
    assert s["pick_correct"] is True
    assert s["brier_score"] is not None


def test_score_card_aggregates():
    per_fight = [
        {"scoring": {"pick_correct": True, "brier_score": 0.10,
                     "line_beat": {"bet_signal": "back_f1",
                                   "would_have_been_profitable": True,
                                   "f1_implied_prob_at_close": 0.60}}},
        {"scoring": {"pick_correct": False, "brier_score": 0.40,
                     "line_beat": {"bet_signal": "back_f2",
                                   "would_have_been_profitable": False,
                                   "f1_implied_prob_at_close": 0.55}}},
        {"scoring": {"pick_correct": True, "brier_score": 0.15,
                     "line_beat": {"bet_signal": "pass",
                                   "would_have_been_profitable": None,
                                   "f1_implied_prob_at_close": 0.50}}},
    ]
    rollup = score_card(per_fight)
    assert rollup["fights_scored"] == 3
    assert rollup["pick_accuracy"] == pytest.approx(2 / 3)
    assert rollup["avg_brier"] == pytest.approx((0.10 + 0.40 + 0.15) / 3)
    assert rollup["betting_record"]["bets_taken"] == 2
    assert rollup["betting_record"]["bets_won"] == 1
```

- [ ] **Step 2: Run tests to verify they all fail with ImportError**

Run from project root:

```bash
pytest backend/reflection/tests/test_score.py -v
```

Expected: All 13 tests FAIL with `ModuleNotFoundError: No module named 'backend.reflection.score'` or `ImportError`.

- [ ] **Step 3: Implement `score.py`**

Create `backend/reflection/score.py`:

```python
"""Deterministic scoring for a single completed UFC fight. Pure Python — no
LLM, no network calls. Fully unit-testable.

Inputs:
- predicted: dict from analyses.json `bets` block, normalized to top-level
  {winner, win_prob, method, rounds} where method has ko_tko/submission/decision
  and rounds has ends_round_1..ends_round_4_or_later + goes_to_decision.
- actual: dict from outcome_scraper {winner, method, round, time, stats}.
  method is one of "KO/TKO", "Submission", "Decision". round=None for decisions.
- closing_line: dict {f1_moneyline, f1_implied_prob} or None.

Outputs the `scoring` block defined in the spec.
"""

from __future__ import annotations

import math
from typing import Any

EDGE_THRESHOLD = 0.05  # |our_prob - closing_implied| <= this -> "pass"


def _predicted_method(predicted: dict) -> str:
    """Return the method label with the highest probability."""
    methods = predicted.get("method", {})
    if not methods:
        return "Decision"
    labels = {"ko_tko": "KO/TKO", "submission": "Submission", "decision": "Decision"}
    best_key = max(methods, key=methods.get)
    return labels.get(best_key, "Decision")


def _predicted_round(predicted: dict) -> str:
    """Return 'decision' or 'R<n>' for the highest-prob round bucket."""
    rounds = predicted.get("rounds", {})
    if not rounds:
        return "decision"
    candidates = {
        "decision": rounds.get("goes_to_decision", 0.0),
        "R1": rounds.get("ends_round_1", 0.0),
        "R2": rounds.get("ends_round_2", 0.0),
        "R3": rounds.get("ends_round_3", 0.0),
        "R4+": rounds.get("ends_round_4_or_later", 0.0),
    }
    return max(candidates, key=candidates.get)


def _actual_round_bucket(actual: dict) -> str:
    """Map actual outcome to the same bucket scheme as _predicted_round."""
    if actual.get("method", "").lower() == "decision":
        return "decision"
    r = actual.get("round")
    if r == 1:
        return "R1"
    if r == 2:
        return "R2"
    if r == 3:
        return "R3"
    if isinstance(r, int) and r >= 4:
        return "R4+"
    return "decision"  # fallback for missing data


def _we_said_f1_prob(predicted: dict, fighter1: str) -> float:
    """Normalize our prediction to fighter1's win probability."""
    if predicted.get("winner") == fighter1:
        return float(predicted.get("win_prob", 0.5))
    return 1.0 - float(predicted.get("win_prob", 0.5))


def _moneyline_payout(implied_prob: float) -> float:
    """$100 unit at the given implied probability — profit if it wins."""
    if implied_prob <= 0 or implied_prob >= 1:
        return 0.0
    return 100.0 * (1.0 - implied_prob) / implied_prob


def score_fight(
    fighter1: str,
    fighter2: str,
    predicted: dict,
    actual: dict,
    closing_line: dict | None,
) -> dict[str, Any]:
    """Compute the per-fight scoring block."""
    pick_correct = predicted.get("winner") == actual.get("winner")

    # Brier score is relative to fighter1's outcome (binary).
    we_said_f1 = _we_said_f1_prob(predicted, fighter1)
    f1_won = 1.0 if actual.get("winner") == fighter1 else 0.0
    brier = (we_said_f1 - f1_won) ** 2

    # Log loss: penalize confident-wrong harder. Clip to avoid log(0).
    p = max(0.001, min(0.999, we_said_f1 if f1_won else 1.0 - we_said_f1))
    log_loss = -math.log(p)

    method_correct = _predicted_method(predicted) == actual.get("method")
    round_correct = _predicted_round(predicted) == _actual_round_bucket(actual)

    if closing_line is None:
        line_beat = None
    else:
        closing_implied = float(closing_line.get("f1_implied_prob", 0.5))
        edge = we_said_f1 - closing_implied
        if abs(edge) <= EDGE_THRESHOLD:
            bet_signal = "pass"
            profitable = None
        elif edge > 0:
            bet_signal = "back_f1"
            profitable = (actual.get("winner") == fighter1)
        else:
            bet_signal = "back_f2"
            profitable = (actual.get("winner") == fighter2)

        line_beat = {
            "we_said_f1_prob": round(we_said_f1, 4),
            "closing_implied_prob": round(closing_implied, 4),
            "edge_pct": round(edge * 100, 2),
            "bet_signal": bet_signal,
            "would_have_been_profitable": profitable,
            "f1_implied_prob_at_close": round(closing_implied, 4),  # alias for rollup
        }

    return {
        "pick_correct": pick_correct,
        "method_correct": method_correct,
        "round_correct": round_correct,
        "brier_score": round(brier, 4),
        "log_loss": round(log_loss, 4),
        "line_beat": line_beat,
    }


def score_card(per_fight_blocks: list[dict]) -> dict[str, Any]:
    """Aggregate per-fight scoring into card-level rollup.

    Each item in per_fight_blocks must have a `scoring` key (matching the
    output of score_fight)."""
    scorings = [b["scoring"] for b in per_fight_blocks]
    n = len(scorings)
    if n == 0:
        return {"fights_scored": 0}

    pick_count = sum(1 for s in scorings if s["pick_correct"])
    brier_total = sum(s["brier_score"] for s in scorings)

    bets = [s["line_beat"] for s in scorings
            if s["line_beat"] is not None and s["line_beat"]["bet_signal"] != "pass"]
    bets_taken = len(bets)
    bets_won = sum(1 for b in bets if b["would_have_been_profitable"])

    # Hypothetical $100 unit P/L
    pl = 0.0
    for b in bets:
        if b["would_have_been_profitable"]:
            # We bet on the side we said was undervalued; payoff at closing line
            implied = b["f1_implied_prob_at_close"] if b["bet_signal"] == "back_f1" \
                else 1.0 - b["f1_implied_prob_at_close"]
            pl += _moneyline_payout(implied)
        else:
            pl -= 100.0

    roi_pct = (pl / (bets_taken * 100.0) * 100) if bets_taken > 0 else 0.0

    return {
        "fights_scored": n,
        "pick_accuracy": round(pick_count / n, 4),
        "avg_brier": round(brier_total / n, 4),
        "betting_record": {
            "bets_taken": bets_taken,
            "bets_won": bets_won,
            "roi_pct": round(roi_pct, 2),
            "unit_pl": round(pl, 2),
        },
    }
```

- [ ] **Step 4: Run tests to verify they all pass**

```bash
pytest backend/reflection/tests/test_score.py -v
```

Expected: All 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/reflection/score.py backend/reflection/tests/test_score.py
git commit -m "Add deterministic scoring layer for post-event reflection"
```

---

## Task 3: Lesson store (TDD)

**Files:**
- Create: `backend/reflection/lesson_store.py`
- Create: `backend/reflection/tests/test_lesson_store.py`

- [ ] **Step 1: Write failing tests**

Create `backend/reflection/tests/test_lesson_store.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest backend/reflection/tests/test_lesson_store.py -v
```

Expected: All 7 tests FAIL with import errors.

- [ ] **Step 3: Implement `lesson_store.py`**

Create `backend/reflection/lesson_store.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest backend/reflection/tests/test_lesson_store.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Seed the empty lessons.json**

Create `backend/cache/lessons.json` with:

```json
{
  "schema_version": 1,
  "last_updated": null,
  "lessons": [],
  "watchlist": [],
  "archived": []
}
```

This file is the source of truth for injection. It must exist before any agent run tries to read it.

- [ ] **Step 6: Commit**

```bash
git add backend/reflection/lesson_store.py backend/reflection/tests/test_lesson_store.py backend/cache/lessons.json
git commit -m "Add lesson store (read/write/regenerate) with seeded empty corpus"
```

---

## Task 4: Outcome scraper (smoke-tested)

**Files:**
- Create: `backend/reflection/outcome_scraper.py`

- [ ] **Step 1: Inspect the existing UFC card scraper for HTML conventions**

Read [backend/tools/scrape_ufc_card.py](../../../backend/tools/scrape_ufc_card.py) — specifically the `_parse_fights_from_event_page` function (or equivalent). The completed-event page has the same structure as the upcoming-event page PLUS result columns: winner highlighted, method, round, time.

- [ ] **Step 2: Implement `outcome_scraper.py`**

Create `backend/reflection/outcome_scraper.py`:

```python
"""Scrape actual fight outcomes for a completed UFC event from ufcstats.com.

Returns per-fight: winner name, method (KO/TKO | Submission | Decision),
round (int or None for decisions), finish time, and basic post-fight stats
(significant strikes, takedowns, knockdowns, sub attempts).

The event page (event-details/<id>) shows a results table with these columns.
"""

from __future__ import annotations

import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ufc-reflection-bot)"}
TIMEOUT = 20


def _get(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def _parse_method(cell_text: str) -> str:
    """Map a method cell to a canonical label."""
    t = cell_text.upper()
    if "SUB" in t:
        return "Submission"
    if "KO" in t or "TKO" in t:
        return "KO/TKO"
    if "DEC" in t or "DECISION" in t:
        return "Decision"
    if "DQ" in t or "NC" in t:
        return "Other"
    return "Decision"  # default


def scrape_event_results(event_url: str) -> dict:
    """Scrape per-fight outcomes from a completed event page.

    Returns:
        {
            "event_url": str,
            "fights": [
                {
                    "fighter1": str,
                    "fighter2": str,
                    "winner": str,            # one of the two fighters
                    "method": str,            # KO/TKO | Submission | Decision | Other
                    "round": int | None,
                    "time": str,              # "MM:SS"
                    "stats": {
                        "sig_strikes_f1": int,
                        "sig_strikes_f2": int,
                        "takedowns_f1": int,
                        "takedowns_f2": int,
                        "knockdowns_f1": int,
                        "knockdowns_f2": int,
                        "sub_attempts_f1": int,
                        "sub_attempts_f2": int,
                    },
                },
                ...
            ],
        }
    """
    html = _get(event_url)
    soup = BeautifulSoup(html, "html.parser")

    fights = []
    rows = soup.select("tr.b-fight-details__table-row__hover")
    for row in rows:
        cells = row.select("td")
        if len(cells) < 7:
            continue
        # Cell 0: W/L marker; Cell 1: fighter names (2 stacked); Cell 6: round; cell 7: time; cell 8 (or last): method (varies)
        names = [a.get_text(strip=True) for a in cells[1].select("a")]
        if len(names) != 2:
            continue
        fighter1, fighter2 = names

        # Winner: the fighter whose name's <p> has class containing "win" — or look at first cell's icon
        winner = None
        first_cell_text = cells[0].get_text(strip=True).upper()
        if "WIN" in first_cell_text or first_cell_text == "W":
            winner = fighter1   # ufcstats orders winner first in the names column
        else:
            # Fallback: scan for "i-win" icon in the names cell
            win_marker = cells[1].select_one(".b-fight-details__person-status_style_green")
            winner = fighter1 if win_marker else fighter2

        # Method
        method_text = ""
        for cell in cells:
            if "method" in (cell.get("class") or []):
                method_text = cell.get_text(strip=True)
                break
        if not method_text:
            # Fallback: try positional — method is usually the second-to-last cell
            method_text = cells[-2].get_text(strip=True) if len(cells) >= 2 else ""
        method = _parse_method(method_text)

        # Round
        round_num = None
        for cell in cells[-4:]:
            txt = cell.get_text(strip=True)
            if txt.isdigit() and 1 <= int(txt) <= 5:
                round_num = int(txt)
                break

        # Time
        time_str = "0:00"
        for cell in cells[-3:]:
            txt = cell.get_text(strip=True)
            if re.match(r"^\d+:\d{2}$", txt):
                time_str = txt
                break

        # Per-fight stat blocks live in nested rows; many event pages only
        # show summary stats per fight. We capture what's visible and leave
        # the rest as zeros — sig strikes columns are usually present.
        stats = {
            "sig_strikes_f1": 0, "sig_strikes_f2": 0,
            "takedowns_f1": 0, "takedowns_f2": 0,
            "knockdowns_f1": 0, "knockdowns_f2": 0,
            "sub_attempts_f1": 0, "sub_attempts_f2": 0,
        }
        # Look for stat cells with two stacked <p> per fighter
        stat_cells = cells[2:6]  # KD, Str, Td, Sub cells in standard layout
        keys_in_order = ["knockdowns", "sig_strikes", "takedowns", "sub_attempts"]
        for cell, key in zip(stat_cells, keys_in_order):
            paragraphs = [p.get_text(strip=True) for p in cell.select("p")]
            if len(paragraphs) >= 2:
                try:
                    stats[f"{key}_f1"] = int(paragraphs[0])
                    stats[f"{key}_f2"] = int(paragraphs[1])
                except ValueError:
                    pass

        if method == "Decision":
            round_num = None  # decisions don't end in a round

        fights.append({
            "fighter1": fighter1,
            "fighter2": fighter2,
            "winner": winner,
            "method": method,
            "round": round_num,
            "time": time_str,
            "stats": stats,
        })

    return {"event_url": event_url, "fights": fights}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m backend.reflection.outcome_scraper <event_url>")
        sys.exit(1)
    import json
    result = scrape_event_results(sys.argv[1])
    print(json.dumps(result, indent=2))
```

- [ ] **Step 3: Smoke test against a recently completed event**

Pick a known completed event URL from ufcstats.com (e.g., the most recent UFC 328 event URL stored in `backend/cache/analyses.json` for the previous event_key, or look it up manually).

Run:

```bash
python -m backend.reflection.outcome_scraper http://www.ufcstats.com/event-details/9eedac48b497de5a
```

Expected: JSON output listing every fight from that event with `winner`, `method`, `round`, `time`. Manually compare against the event page in a browser — at minimum the main-event winner and method should match.

If the scraper returns 0 fights or wrong winners, debug the cell-index assumptions before continuing.

- [ ] **Step 4: Commit**

```bash
git add backend/reflection/outcome_scraper.py
git commit -m "Add UFCstats event-results scraper"
```

---

## Task 5: Closing-line scraper (per-card wrapper)

**Files:**
- Create: `backend/reflection/closing_line_scraper.py`

- [ ] **Step 1: Implement card-level wrapper**

The existing [scrape_bestfightodds.py](../../../backend/tools/scrape_bestfightodds.py) handles ONE fighter pair at a time. We need a wrapper that takes the full card and returns closing lines for every fight.

Create `backend/reflection/closing_line_scraper.py`:

```python
"""Scrape closing moneylines for every fight on a completed UFC card from
BestFightOdds. Per fight, returns the most recent line we can find (treating
it as the closing line since the event is already over)."""

from __future__ import annotations

import sys
import os
import time

# Reuse the existing single-fight BFO scraper
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(BACKEND_DIR, "tools"))
from scrape_bestfightodds import scrape_line_movement  # noqa: E402


def _moneyline_to_implied_prob(ml: int) -> float:
    """Convert American moneyline to implied probability."""
    if ml < 0:
        return -ml / (-ml + 100)
    return 100 / (ml + 100)


def scrape_card_closing_lines(fights: list[dict], delay_sec: float = 1.0) -> dict:
    """Args:
        fights: list of dicts each with at least {fighter1, fighter2}.

    Returns:
        {
            fight_key: {
                "f1_moneyline": int | None,
                "f1_implied_prob": float | None,
                "source": "bestfightodds",
                "scraped_at": iso8601 str,
            },
            ...
        }
    fight_key is "<f1>__<f2>" (slug-style). Entries with no data have None values.
    """
    import datetime as _dt
    out = {}
    for f in fights:
        f1, f2 = f["fighter1"], f["fighter2"]
        key = f"{f1}__{f2}"
        lm = None
        try:
            lm = scrape_line_movement(f1, f2)
        except Exception as e:
            print(f"  closing line scrape failed for {f1} vs {f2}: {e!r}", file=sys.stderr)
        time.sleep(delay_sec)

        if not lm or f1 not in lm:
            out[key] = {
                "f1_moneyline": None,
                "f1_implied_prob": None,
                "source": "bestfightodds",
                "scraped_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            }
            continue

        # Treat 'current' as closing line (event is already over)
        f1_ml = lm[f1].get("current")
        out[key] = {
            "f1_moneyline": f1_ml,
            "f1_implied_prob": _moneyline_to_implied_prob(f1_ml) if f1_ml is not None else None,
            "source": "bestfightodds",
            "scraped_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }
    return out
```

- [ ] **Step 2: Smoke test**

Run from project root in a Python REPL or script:

```python
from backend.reflection.closing_line_scraper import scrape_card_closing_lines
result = scrape_card_closing_lines([
    {"fighter1": "Arnold Allen", "fighter2": "Melquizael Costa"}
])
print(result)
```

Expected: dict with one key `Arnold Allen__Melquizael Costa`, containing either real moneyline values or `None` (if BFO doesn't have data). The function MUST NOT raise.

- [ ] **Step 3: Commit**

```bash
git add backend/reflection/closing_line_scraper.py
git commit -m "Add card-level closing-line scraper wrapper"
```

---

## Task 6: Detect completed events

**Files:**
- Create: `backend/reflection/detect_completed_events.py`

- [ ] **Step 1: Implement detection**

Create `backend/reflection/detect_completed_events.py`:

```python
"""Find UFC events that completed in the past N days AND that we have
predictions for in backend/cache/analyses.json."""

from __future__ import annotations

import datetime
import json
import os
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
```

- [ ] **Step 2: Smoke test**

```bash
python -m backend.reflection.detect_completed_events
```

Expected: JSON array of zero or more events. If the latest analyzed event (in `backend/cache/analyses.json`) is now in the past, it should appear here.

- [ ] **Step 3: Commit**

```bash
git add backend/reflection/detect_completed_events.py
git commit -m "Add event-completion detection (cross-references prediction cache)"
```

---

## Task 7: Reflection prompts

**Files:**
- Create: `backend/reflection/prompts/__init__.py` (empty)
- Create: `backend/reflection/prompts/per_fight_reflection.md`
- Create: `backend/reflection/prompts/card_meta_pass.md`
- Create: `backend/reflection/prompts/lesson_merge.md`

- [ ] **Step 1: Create the prompts directory and per-fight prompt**

Create `backend/reflection/prompts/__init__.py` as empty file.

Create `backend/reflection/prompts/per_fight_reflection.md`:

````markdown
You are a post-fight reviewer for a UFC fight-prediction system that uses 10 specialist agents (5 offense, 5 defense across striking, wrestling, takedowns, grappling, submissions) plus a synthesizer.

You will be given ONE completed fight:
1. The 20 specialist agent reports we generated before the fight (10 for fighter1 as primary, 10 for fighter2 as primary)
2. The synthesizer's final prediction (winner, win_prob, method probs, round probs, supporting narrative)
3. The actual outcome (winner, method, round, time, post-fight stats)
4. A deterministic scoring block (pick_correct, method_correct, round_correct, brier_score, line_beat)

Your job is to identify *specific, falsifiable patterns* in the specialists' reasoning that, if corrected, would have produced a more accurate prediction. The patterns must be repeatable — things that could go wrong the same way in future similar matchups, NOT one-off events.

## Output format

Emit ONE fenced ```json``` block with this exact shape:

```json
{
  "findings": [
    {
      "responsible_agents": ["<agent-id>", ...],
      "pattern": "<concrete, falsifiable pattern, 1-2 sentences>",
      "evidence_excerpt": "<exact quote from one specialist report showing the error>",
      "what_actually_happened": "<what the post-fight stats/outcome show>",
      "suggested_correction": "<actionable correction for the agent's reasoning, 1 sentence>",
      "confidence_for_this_fight": "low" | "medium" | "high"
    }
  ]
}
```

Then below the JSON, emit a 100-200 word plain-English narrative explaining your reasoning. The narrative is for human review; it does not affect downstream processing.

## Rules

1. **No findings ≠ failure.** If we predicted correctly AND for the right reasons, output `{"findings": []}` followed by a one-sentence narrative confirming the prediction was sound.
2. **Concrete > abstract.** "Striking-offense over-rated Allen's counter-strike output against high-volume pressure fighters" beats "We should weight cardio more."
3. **Quote evidence.** Every finding must include `evidence_excerpt` — an actual sentence or rating from one specialist's report. If you can't quote it, the finding is too vague.
4. **One pattern per finding.** Don't combine multiple errors into one "finding."
5. **Confidence_for_this_fight** reflects how robust THIS observation is, not the cross-fight pattern strength. The cross-fight confidence is determined by the merge pass based on how many times this pattern recurs.
6. **Valid agent IDs** are: ufc-striking-offense, ufc-striking-defense, ufc-wrestling-offense, ufc-wrestling-defense, ufc-takedown-offense, ufc-takedown-defense, ufc-grappling-offense, ufc-grappling-defense, ufc-submission-offense, ufc-submission-defense, synthesizer.
7. **Output ONLY** the JSON block and the narrative. No preamble.
````

- [ ] **Step 2: Create the card meta-pass prompt**

Create `backend/reflection/prompts/card_meta_pass.md`:

````markdown
You are aggregating per-fight reflection findings from a single completed UFC card into card-level patterns.

You will be given:
1. The card-level scoring rollup (pick accuracy, average Brier, betting record)
2. The per-fight `findings` from every fight on the card

Your job is to identify which findings are **cross-fight patterns** (the same kind of reasoning error showed up on multiple fights) versus which are **one-off observations**.

## Output format

Emit ONE fenced ```json``` block:

```json
{
  "card_level_findings": [
    {
      "responsible_agents": ["<agent-id>", ...],
      "pattern": "<1-2 sentence pattern that shows up across multiple fights>",
      "fights_supporting": ["<fight_key>", ...],
      "confidence_for_this_card": "low" | "medium" | "high",
      "suggested_correction": "<single actionable correction>"
    }
  ],
  "single_fight_findings": [
    {
      "responsible_agents": [...],
      "pattern": "...",
      "fight_key": "...",
      "suggested_correction": "..."
    }
  ]
}
```

Then below the JSON, emit a 100-200 word card-level narrative.

## Rules

1. A finding is **cross-fight** if it appears in ≥2 fights. Otherwise it's **single_fight**.
2. `confidence_for_this_card` for cross-fight findings: "high" if ≥3 fights support it, "medium" if 2, "low" if all single_fight.
3. Don't fabricate connections. If only one fight had a particular finding, it stays in `single_fight_findings`.
4. Pull through the same agent IDs from the per-fight findings. Don't invent new ones.
5. Output ONLY the JSON block and the narrative.
````

- [ ] **Step 3: Create the lesson-merge prompt**

Create `backend/reflection/prompts/lesson_merge.md`:

````markdown
You are the curator of a long-running lessons-learned corpus for a UFC fight-prediction system. The corpus is a JSON file with three buckets: `lessons` (active, high-confidence, injected into agent prompts), `watchlist` (candidate patterns), and `archived` (inactive, retained for audit).

You will be given:
1. The CURRENT lessons.json
2. NEW findings from the latest reflected event (card-level + single-fight)
3. Event metadata (event_key, event_date)

Your job: produce the UPDATED lessons.json. Output ONLY the updated JSON in a single fenced ```json``` block. No prose, no narrative.

## Curation rules — enforce these strictly

1. **Match before adding.** For each new finding, check if it matches an existing entry in `lessons` or `watchlist`. Match by pattern semantics (do they describe the same kind of error?), NOT by exact text. If you find a match:
   - Increment `evidence_count` by 1
   - Update `last_confirmed` to the new event_date
   - APPEND (do not replace) a new example to `examples[]` with: event_key, fight_key (or "card-level"), what_we_said, what_happened
   - Do NOT modify pattern text unless the match clarifies it

2. **Add genuinely new findings to `watchlist`** with:
   - `confidence`: "low"
   - `evidence_count`: 1
   - `first_seen` and `last_confirmed`: the new event_date
   - `status`: "watching"
   - One initial example
   - Generate a new unique id: `watch_NNN` where NNN is the next available number across both `lessons` and `watchlist`

3. **Promote watchlist → lessons** when:
   - `evidence_count >= 3`
   - AND `last_confirmed` is within the past 8 weeks of the event_date
   - When promoting: set `confidence: "high"`, `status: "active"`, change the id prefix from `watch_` to `lesson_`

4. **Archive lessons** when:
   - `last_confirmed` is more than 6 months before the event_date
   - When archiving: set `status: "archived"`, add `archived_at: <event_date>`, add `archived_reason` field
   - Move the entry from `lessons` to `archived`

5. **NEVER delete `examples`** — only append. The audit trail must persist.

6. **NEVER modify the `id` of an existing entry** (except the prefix change during promotion).

7. **Set `last_updated`** to the event's `reflected_at` timestamp.

## Output

Single fenced ```json``` block containing the complete updated lessons.json. Schema:

```json
{
  "schema_version": 1,
  "last_updated": "<ISO8601>",
  "lessons": [...],
  "watchlist": [...],
  "archived": [...]
}
```

Output NOTHING but this JSON block.
````

- [ ] **Step 4: Commit**

```bash
git add backend/reflection/prompts/
git commit -m "Add three reflection prompts (per-fight, card meta, lesson merge)"
```

---

## Task 8: Reflection runner (three Opus passes)

**Files:**
- Create: `backend/reflection/reflect_runner.py`

- [ ] **Step 1: Implement the runner**

Create `backend/reflection/reflect_runner.py`:

```python
"""The three-pass Opus reflection pipeline:

  1. Per-fight reflection — 13 parallel Opus calls
  2. Card meta-pass — 1 Opus call aggregating per-fight findings
  3. Lesson merge — 1 Opus call rewriting lessons.json

Each LLM client uses timeout=300.0 per the project convention; agent_runner.py
has the long-running notes on why this matters.
"""

from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DEFAULT_MODEL = "claude-opus-4-7"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _extract_json(text: str) -> dict:
    """Extract the first ```json``` fenced block from LLM output."""
    m = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if not m:
        # Try raw JSON
        m2 = re.search(r"(\{.*\})", text, re.DOTALL)
        if not m2:
            raise ValueError("No JSON found in LLM response")
        return json.loads(m2.group(1))
    return json.loads(m.group(1))


def _call_opus(
    client: anthropic.Anthropic,
    system_prompt: str,
    user_payload: dict,
    max_tokens: int = 4096,
    max_retries: int = 3,
) -> dict:
    """Call Opus with retry on JSON parse error or transient failures.
    Returns the parsed JSON object."""
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            msg = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}],
            )
            text = msg.content[0].text
            return _extract_json(text)
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            print(f"  reflect: JSON parse error attempt {attempt + 1}: {e!r}", file=sys.stderr)
        except anthropic.APIError as e:
            last_err = e
            print(f"  reflect: API error attempt {attempt + 1}: {e!r}", file=sys.stderr)
        # Exponential backoff between retries
        import time as _t
        _t.sleep(2 ** attempt)
    raise RuntimeError(f"reflect: all {max_retries} retries failed; last error: {last_err!r}")


def reflect_per_fight(
    client: anthropic.Anthropic,
    fight_blocks: list[dict],
    max_workers: int = 5,
) -> list[dict]:
    """Run per-fight reflection in parallel.

    Each fight_block must contain:
        fight_key, fighter1, fighter2, predicted, actual, closing_line,
        scoring, specialist_reports (dict of agent_name -> report),
        synthesizer_output
    """
    system_prompt = _load_prompt("per_fight_reflection")

    def _one(fb: dict) -> dict:
        try:
            findings = _call_opus(client, system_prompt, fb, max_tokens=4096)
        except Exception as e:
            print(f"  reflect: fight {fb['fight_key']} fell back to empty: {e!r}", file=sys.stderr)
            findings = {"findings": []}
        return {"fight_key": fb["fight_key"], **findings}

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_one, fb): fb["fight_key"] for fb in fight_blocks}
        for fut in as_completed(futures):
            results.append(fut.result())
    # Preserve input order
    by_key = {r["fight_key"]: r for r in results}
    return [by_key[fb["fight_key"]] for fb in fight_blocks]


def reflect_card_meta(
    client: anthropic.Anthropic,
    event_key: str,
    card_rollup: dict,
    per_fight_findings: list[dict],
) -> dict:
    """Aggregate per-fight findings into card-level patterns."""
    system_prompt = _load_prompt("card_meta_pass")
    payload = {
        "event_key": event_key,
        "card_rollup": card_rollup,
        "per_fight_findings": per_fight_findings,
    }
    return _call_opus(client, system_prompt, payload, max_tokens=6144)


def merge_lessons(
    client: anthropic.Anthropic,
    current_lessons: dict,
    new_card_findings: dict,
    event_metadata: dict,
) -> dict:
    """Run the lesson-merge pass and return the updated lessons.json content."""
    system_prompt = _load_prompt("lesson_merge")
    payload = {
        "current_lessons": current_lessons,
        "new_card_findings": new_card_findings,
        "event_metadata": event_metadata,
    }
    return _call_opus(client, system_prompt, payload, max_tokens=16384)


def build_anthropic_client(timeout_sec: float = 300.0) -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        timeout=timeout_sec,
    )
```

- [ ] **Step 2: Quick syntax/import check**

```bash
python -c "from backend.reflection.reflect_runner import reflect_per_fight, reflect_card_meta, merge_lessons; print('OK')"
```

Expected: prints `OK`.

- [ ] **Step 3: Commit**

```bash
git add backend/reflection/reflect_runner.py
git commit -m "Add three-pass Opus reflection runner (per-fight, card meta, lesson merge)"
```

---

## Task 9: CLI entry — `__main__.py`

**Files:**
- Create: `backend/reflection/__main__.py`

- [ ] **Step 1: Implement the orchestrator**

Create `backend/reflection/__main__.py`:

```python
"""CLI entry for the reflection pipeline. Wires up:

  detect → scrape outcomes + closing lines → score → reflect (3 passes)
  → write lessons.json + lessons.md + scores/<event_key>.json + append metrics_log.jsonl
  → git add/commit/push

Usage:
  python -m backend.reflection                  # auto-detect events, real run
  python -m backend.reflection --dry-run        # detect + score + reflect, NO writes
  python -m backend.reflection --event-key KEY  # force a specific event
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_DIR.parent / ".env")  # workspace .env

# Match the refresh_cache.py pattern: BACKEND_DIR on sys.path so we can import
# `cache` (the file, not the directory) and reuse its fight_key helper. This
# avoids the ambiguity between `backend/cache.py` and `backend/cache/`.
sys.path.insert(0, str(BACKEND_DIR))

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
    sys.exit(2)

from cache import fight_key  # noqa  — from backend/cache.py, the existing helper
from backend.reflection.detect_completed_events import find_events_to_reflect_on  # noqa
from backend.reflection.outcome_scraper import scrape_event_results  # noqa
from backend.reflection.closing_line_scraper import scrape_card_closing_lines  # noqa
from backend.reflection.score import score_fight, score_card  # noqa
from backend.reflection.reflect_runner import (  # noqa
    reflect_per_fight, reflect_card_meta, merge_lessons, build_anthropic_client,
)
from backend.reflection.lesson_store import (  # noqa
    load_lessons, save_lessons, save_markdown,
)

CACHE_DIR = BACKEND_DIR / "cache"
SCORES_DIR = CACHE_DIR / "scores"
LESSONS_JSON = CACHE_DIR / "lessons.json"
LESSONS_MD = CACHE_DIR / "lessons.md"
METRICS_LOG = CACHE_DIR / "metrics_log.jsonl"
ANALYSES_JSON = CACHE_DIR / "analyses.json"


def _load_predictions(event_key: str) -> dict | None:
    if not ANALYSES_JSON.exists():
        return None
    with ANALYSES_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("event_key") != event_key:
        return None
    return data


def _build_fight_blocks(predictions: dict, outcomes: dict, closing_lines: dict) -> list[dict]:
    """Join predictions, outcomes, and closing_lines by fighter pair using
    the existing slug-based, order-independent fight_key helper."""
    blocks = []
    pred_fights = predictions.get("fights", {})
    for o in outcomes.get("fights", []):
        f1, f2 = o["fighter1"], o["fighter2"]
        # cache.fight_key is order-independent and slug-based, so this matches
        # however the prediction was originally stored.
        key = fight_key(f1, f2)
        pred = pred_fights.get(key)
        if not pred:
            print(f"  no prediction found for {f1} vs {f2} (key={key!r}), skipping", file=sys.stderr)
            continue

        bets = pred.get("bets", {})
        moneyline = bets.get("moneyline", {})
        prediction_normalized = {
            "winner": moneyline.get("pick"),
            "win_prob": moneyline.get("win_prob"),
            "method": bets.get("method", {}),
            "rounds": {
                **bets.get("rounds", {}),
                "goes_to_decision": bets.get("distance", {}).get("goes_to_decision", 0.0),
            },
        }

        # closing_lines is keyed by the raw (f1, f2) order from outcomes
        closing_key = f"{f1}__{f2}"
        line = closing_lines.get(closing_key)
        line_for_score = line if line and line.get("f1_implied_prob") is not None else None
        scoring = score_fight(f1, f2, prediction_normalized, o, line_for_score)

        blocks.append({
            "fight_key": key,
            "fighter1": f1,
            "fighter2": f2,
            "predicted": prediction_normalized,
            "actual": o,
            "closing_line": line,
            "scoring": scoring,
            "specialist_reports": pred.get("specialist_reports", {}),
            "synthesizer_output": pred.get("analysis_sections", {}),
        })
    return blocks


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit_and_push(paths: list[str], message: str) -> None:
    add = _git("add", "--", *paths)
    if add.returncode != 0:
        print(f"git add failed: {add.stderr}", file=sys.stderr)
        return
    diff = _git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("No reflection changes to commit")
        return
    commit = _git("commit", "-m", message)
    if commit.returncode != 0:
        print(f"git commit failed: {commit.stderr}", file=sys.stderr)
        return
    print(commit.stdout.strip())
    push = _git("push")
    if push.returncode != 0:
        # Same rebase-on-conflict pattern as refresh_cache.py
        print(f"git push rejected, attempting rebase: {push.stderr.strip()}", file=sys.stderr)
        _git("fetch", "origin")
        rebase = _git("rebase", "origin/master")
        if rebase.returncode != 0:
            print(f"git rebase failed: {rebase.stderr}", file=sys.stderr)
            _git("rebase", "--abort")
            return
        push = _git("push")
        if push.returncode != 0:
            print(f"git push failed after rebase: {push.stderr}", file=sys.stderr)
            return
    print("Pushed to origin")


def _print_delta_summary(prev: dict, new: dict) -> None:
    """Compare two lessons stores and print a GHA-friendly summary."""
    prev_ids = {l["id"] for l in prev.get("lessons", []) + prev.get("watchlist", [])}
    new_ids = {l["id"] for l in new.get("lessons", []) + new.get("watchlist", [])}
    added = new_ids - prev_ids
    promoted = []
    for l in new.get("lessons", []):
        if l["id"].startswith("lesson_"):
            # Was it in watchlist before?
            for pw in prev.get("watchlist", []):
                if pw["id"].replace("watch_", "lesson_") == l["id"]:
                    promoted.append(l["id"])
                    break

    print("=== Reflection delta ===")
    print(f"  new findings: {len(added)}")
    print(f"  promoted to active: {len(promoted)}")
    print(f"  total active lessons: {len(new.get('lessons', []))}")
    print(f"  total watchlist: {len(new.get('watchlist', []))}")
    print(f"  total archived: {len(new.get('archived', []))}")


def run_reflection_for_event(event: dict, dry_run: bool = False) -> bool:
    """Reflect on one event. Returns True on success."""
    event_key = event["event_key"]
    print(f"=== Reflecting on {event_key} ===")

    predictions = _load_predictions(event_key)
    if predictions is None:
        print(f"  no predictions cached for {event_key}, skipping", file=sys.stderr)
        return False

    print("  scraping outcomes...")
    outcomes = scrape_event_results(event["event_url"])
    if not outcomes.get("fights"):
        print("  no outcomes parsed, skipping", file=sys.stderr)
        return False

    print("  scraping closing lines...")
    closing_lines = scrape_card_closing_lines(outcomes["fights"])

    print("  scoring fights...")
    fight_blocks = _build_fight_blocks(predictions, outcomes, closing_lines)
    if not fight_blocks:
        print("  no fight blocks built, skipping", file=sys.stderr)
        return False

    rollup = score_card(fight_blocks)
    print(f"  card rollup: pick_accuracy={rollup.get('pick_accuracy')}, "
          f"avg_brier={rollup.get('avg_brier')}, "
          f"bets_won={rollup.get('betting_record', {}).get('bets_won')}/"
          f"{rollup.get('betting_record', {}).get('bets_taken')}")

    event_score = {
        "event_key": event_key,
        "event_date": event["event_date"],
        "reflected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "fights": fight_blocks,
        "card_rollup": rollup,
    }

    print("  running per-fight reflection (Opus)...")
    client = build_anthropic_client()
    per_fight_findings = reflect_per_fight(client, fight_blocks, max_workers=5)

    print("  running card meta-pass (Opus)...")
    card_meta = reflect_card_meta(client, event_key, rollup, per_fight_findings)

    print("  running lesson merge (Opus)...")
    current_lessons = load_lessons(LESSONS_JSON)
    new_findings = {
        "per_fight": per_fight_findings,
        "card_meta": card_meta,
    }
    updated_lessons = merge_lessons(
        client, current_lessons, new_findings,
        event_metadata={
            "event_key": event_key,
            "event_date": event["event_date"],
            "reflected_at": event_score["reflected_at"],
        },
    )

    _print_delta_summary(current_lessons, updated_lessons)

    if dry_run:
        print("  --dry-run: not writing any files")
        return True

    # Write artifacts
    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    safe_key = "".join(c if c.isalnum() or c in "_-." else "_" for c in event_key)
    score_path = SCORES_DIR / f"{safe_key}.json"
    with score_path.open("w", encoding="utf-8") as f:
        json.dump(event_score, f, indent=2, default=str)

    save_lessons(LESSONS_JSON, updated_lessons)
    save_markdown(LESSONS_MD, updated_lessons)

    # Append to metrics_log.jsonl
    metrics_row = {
        "event_key": event_key,
        "event_date": event["event_date"],
        "fights_scored": rollup.get("fights_scored"),
        "pick_accuracy": rollup.get("pick_accuracy"),
        "avg_brier": rollup.get("avg_brier"),
        "bets_taken": rollup.get("betting_record", {}).get("bets_taken"),
        "bets_won": rollup.get("betting_record", {}).get("bets_won"),
        "roi_pct": rollup.get("betting_record", {}).get("roi_pct"),
        "reflected_at": event_score["reflected_at"],
    }
    with METRICS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(metrics_row) + "\n")

    # Commit + push
    _commit_and_push(
        paths=[
            str(LESSONS_JSON.relative_to(PROJECT_DIR)),
            str(LESSONS_MD.relative_to(PROJECT_DIR)),
            str(score_path.relative_to(PROJECT_DIR)),
            str(METRICS_LOG.relative_to(PROJECT_DIR)),
        ],
        message=f"reflect: lessons updated for {event_key}",
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the post-event reflection pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Run end-to-end but don't write or commit.")
    parser.add_argument("--event-key", help="Force reflection on a specific event_key.")
    args = parser.parse_args()

    print(f"[{datetime.datetime.now().isoformat()}] reflection starting")

    if args.event_key:
        # Manual run — build a synthetic event dict from analyses.json
        if not ANALYSES_JSON.exists():
            print("ERROR: no analyses.json", file=sys.stderr)
            return 1
        with ANALYSES_JSON.open("r", encoding="utf-8") as f:
            preds = json.load(f)
        if preds.get("event_key") != args.event_key:
            print(f"ERROR: analyses.json has event_key {preds.get('event_key')!r}, not {args.event_key!r}", file=sys.stderr)
            return 1
        # We still need the event_url — derive from card.json or rescrape
        events = find_events_to_reflect_on(lookback_days=180)
        match = next((e for e in events if e["event_key"] == args.event_key), None)
        if not match:
            print(f"ERROR: event_key {args.event_key!r} not found in recent completed events", file=sys.stderr)
            return 1
        events_to_reflect = [match]
    else:
        events_to_reflect = find_events_to_reflect_on()

    if not events_to_reflect:
        print("No completed events to reflect on in the lookback window — exit.")
        return 0

    any_failed = False
    for event in events_to_reflect:
        try:
            ok = run_reflection_for_event(event, dry_run=args.dry_run)
            if not ok:
                any_failed = True
        except Exception as e:
            print(f"ERROR reflecting on {event['event_key']}: {e!r}", file=sys.stderr)
            traceback.print_exc()
            any_failed = True

    print(f"[{datetime.datetime.now().isoformat()}] reflection done")
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Sanity check imports**

```bash
python -m backend.reflection --help
```

Expected: usage help text printed, no import errors.

- [ ] **Step 3: Commit**

```bash
git add backend/reflection/__main__.py
git commit -m "Add reflection CLI entry: detect -> score -> reflect -> publish"
```

---

## Task 10: Lesson injection — `agent_runner.py`

**Files:**
- Modify: `backend/agents/agent_runner.py`
- Create: `backend/reflection/tests/test_inject_lessons.py`

- [ ] **Step 1: Write failing tests**

Create `backend/reflection/tests/test_inject_lessons.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

```bash
pytest backend/reflection/tests/test_inject_lessons.py -v
```

Expected: All 3 tests FAIL with `AttributeError: module 'backend.agents.agent_runner' has no attribute '_inject_lessons'`.

- [ ] **Step 3: Add `_inject_lessons` to `agent_runner.py`**

Modify [backend/agents/agent_runner.py](../../../backend/agents/agent_runner.py).

After the existing imports near the top of the file (around line 18), add:

```python
from pathlib import Path
from backend.reflection.lesson_store import load_lessons, lessons_for_agent

_LESSONS_PATH = Path(__file__).resolve().parent.parent / "cache" / "lessons.json"

_LESSONS_INJECTION_HEADER = """

## Field-tested adjustments from past predictions

The following patterns have been observed in past predictions. Use them as PRIORS that adjust your default reasoning, NOT as overriding rules. If the current dossier directly contradicts a prior, trust the dossier.
"""


def _inject_lessons(system_prompt: str, agent_name: str, max_lessons: int = 5) -> str:
    """Append a 'Field-tested adjustments' section to the system prompt if
    there are relevant high-confidence lessons. Falls back to the original
    prompt unchanged if lessons.json is missing or has no matching entries."""
    try:
        store = load_lessons(_LESSONS_PATH)
    except Exception:
        return system_prompt
    relevant = lessons_for_agent(store, agent_name, max_lessons=max_lessons)
    if not relevant:
        return system_prompt
    parts = [system_prompt, _LESSONS_INJECTION_HEADER]
    for lesson in relevant:
        parts.append(
            f"\n- PATTERN: {lesson.get('pattern', '?')}\n"
            f"  CORRECTION: {lesson.get('suggested_correction', '?')}\n"
            f"  EVIDENCE: {lesson.get('evidence_count', 0)} observations since {lesson.get('first_seen', '?')}"
        )
    return "".join(parts)
```

Then find the `run_one_agent` function (around line 157). At the point where `system_prompt` is loaded from the agent file (around line 169), wrap it:

Find:
```python
    frontmatter, system_prompt, agent_name = load_agent(agent_path)
    user_text = _build_user_payload(primary, opponent, dossier, opponent_dossier)
```

Change to:
```python
    frontmatter, system_prompt, agent_name = load_agent(agent_path)
    system_prompt = _inject_lessons(system_prompt, agent_name)
    user_text = _build_user_payload(primary, opponent, dossier, opponent_dossier)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest backend/reflection/tests/test_inject_lessons.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Run the full pytest suite to confirm no regressions**

```bash
pytest backend/reflection/tests/ -v
```

Expected: All tests across all three test files PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/agents/agent_runner.py backend/reflection/tests/test_inject_lessons.py
git commit -m "Inject high-confidence per-agent lessons into specialist system prompts"
```

---

## Task 11: Lesson injection — `synthesizer.py`

**Files:**
- Modify: `backend/agents/synthesizer.py`

- [ ] **Step 1: Add injection to `synthesizer.py`**

Modify [backend/agents/synthesizer.py](../../../backend/agents/synthesizer.py).

Near the top after existing imports:

```python
from pathlib import Path
from backend.reflection.lesson_store import load_lessons, lessons_for_agent

_LESSONS_PATH = Path(__file__).resolve().parent.parent / "cache" / "lessons.json"


def _inject_synthesizer_lessons(instructions: str, max_lessons: int = 8) -> str:
    """Append synthesizer-relevant lessons (applies_to contains 'synthesizer')."""
    try:
        store = load_lessons(_LESSONS_PATH)
    except Exception:
        return instructions
    relevant = lessons_for_agent(store, "synthesizer", max_lessons=max_lessons)
    if not relevant:
        return instructions
    parts = [instructions,
             "\n\n## Field-tested adjustments from past synthesizer predictions\n",
             "Use these as priors that adjust default reasoning, NOT as overriding rules. If the current matchup contradicts a prior, trust the matchup.\n"]
    for lesson in relevant:
        parts.append(
            f"\n- PATTERN: {lesson.get('pattern', '?')}\n"
            f"  CORRECTION: {lesson.get('suggested_correction', '?')}\n"
            f"  EVIDENCE: {lesson.get('evidence_count', 0)} observations since {lesson.get('first_seen', '?')}"
        )
    return "".join(parts)
```

Find the `synthesize` function (around line 263). Locate where `instructions` is built (around line 277):

```python
    instructions = _OUTPUT_INSTRUCTIONS.format(
        f1_name=f1_dossier["name"], f2_name=f2_dossier["name"]
    )
```

Add right after that line:

```python
    instructions = _inject_synthesizer_lessons(instructions)
```

- [ ] **Step 2: Verify import still works**

```bash
python -c "from backend.agents.synthesizer import synthesize; print('OK')"
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add backend/agents/synthesizer.py
git commit -m "Inject synthesizer-tagged lessons into synthesizer instructions"
```

---

## Task 12: GHA workflow — `reflect.yml`

**Files:**
- Create: `.github/workflows/reflect.yml`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/reflect.yml`:

```yaml
# Post-event reflection. Runs every Sunday at 12:00 UTC. Idempotent: if no
# UFC event completed in the past 7 days that we have predictions for, the
# script exits 0 immediately.
#
# Pipeline (in backend/reflection/__main__.py):
#   detect -> scrape outcomes + closing lines -> deterministic score
#   -> 3 Opus passes (per-fight, card meta, lesson merge)
#   -> commit lessons.json/lessons.md/scores/<event>.json/metrics_log.jsonl
#
# See docs/superpowers/specs/2026-05-11-post-event-reflection-design.md.

name: Reflect on completed UFC card

on:
  schedule:
    - cron: "0 12 * * 0"   # Every Sunday 12:00 UTC (~7 AM CDT)
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Dry run (no writes/commits)?"
        required: false
        default: "false"
      event_key:
        description: "Force reflection on a specific event_key (e.g. ufc-328--chimaev-vs--strickland__May 09, 2026)"
        required: false

permissions:
  contents: write

concurrency:
  group: reflect-card
  cancel-in-progress: false

jobs:
  reflect:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      PYTHONUNBUFFERED: "1"
    steps:
      - name: Check out repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: true

      - name: Configure git author
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt

      - name: Install Python deps
        run: pip install -r backend/requirements.txt

      - name: Run reflection
        run: |
          ARGS=""
          if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
            ARGS="$ARGS --dry-run"
          fi
          if [ -n "${{ github.event.inputs.event_key }}" ]; then
            ARGS="$ARGS --event-key \"${{ github.event.inputs.event_key }}\""
          fi
          eval "python -m backend.reflection $ARGS"
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/reflect.yml
git commit -m "Add Sunday cron workflow that runs the reflection pipeline"
```

---

## Task 13: CLAUDE.md update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add a "Reflection pipeline" section**

In [CLAUDE.md](../../../CLAUDE.md), find the "## Schedule (GitHub Actions cron — `.github/workflows/refresh-card.yml`)" section. Immediately AFTER that section ends, insert:

```markdown
## Reflection pipeline (`.github/workflows/reflect.yml`)

Runs every **Sunday 12:00 UTC** (~7 AM CDT). Idempotent: if no event we predicted on completed in the past 7 days, exits in <30s.

Pipeline (in `backend/reflection/__main__.py`):

1. **Detect** which event(s) we have predictions for that just completed (cross-references `analyses.json` event_key against ufcstats completed-events list).
2. **Scrape** actual outcomes from ufcstats and closing lines from BestFightOdds.
3. **Score** deterministically (no LLM): pick correct?, method correct?, round correct?, Brier score, line-beat ROI. Output: `backend/cache/scores/<event_key>.json`.
4. **Three Opus reflection passes:**
   - Per-fight reflection (13 parallel Opus calls) → structured findings
   - Card meta-pass (1 Opus call) → cross-fight patterns
   - Lesson merge (1 Opus call) → updated `backend/cache/lessons.json`
5. **Commit + push** lessons.json, lessons.md, the event score file, and a new row in `metrics_log.jsonl`.

**How lessons take effect:** `agent_runner.py` and `synthesizer.py` load `lessons.json` on every call and append high-confidence lessons (filtered by `applies_to`) to the system prompt. No manual step needed — the next refresh-card.yml run automatically uses the new lessons.

**Cost:** ~$2.85/event (all Opus). ~$145/year at 1 event/week.

**Manual run:** `gh workflow run reflect.yml --repo zacharytroberts03-ctrl/ufc-11` or `python -m backend.reflection [--dry-run] [--event-key KEY]` from the local backend.

See [docs/superpowers/specs/2026-05-11-post-event-reflection-design.md](docs/superpowers/specs/2026-05-11-post-event-reflection-design.md) for the full design.
```

- [ ] **Step 2: Add don't-do entry**

Find the "## Don't-do-this list" section. Add this entry (anywhere, but ideally near the other "don't manually edit" patterns):

```markdown
- Don't manually edit `backend/cache/lessons.json` — the lesson-merge pass owns it and will overwrite your edits on the next reflection run. If you want to remove a bad lesson, edit `lessons.md` to mark it for review, then drop the corresponding `lessons[]` entry from `lessons.json` in a one-off commit AND add a guardrail to the lesson-merge prompt to keep it out.
```

- [ ] **Step 3: Update the Directory map**

In the "## Directory map" section, find the `.github/workflows/` block and update it. Find:

```
├── .github/workflows/
│   └── refresh-card.yml            ← cron in GitHub Actions (Mon/Wed/Fri) — replaces local Windows task
```

Change to:

```
├── .github/workflows/
│   ├── refresh-card.yml            ← refresh cron (Mon/Wed/Fri) — replaces local Windows task
│   └── reflect.yml                 ← reflection cron (Sun) — turns event outcomes into per-agent lessons
```

Also under `backend/`, find the agents block and add a sibling for reflection. After the `├── agents/` block (which ends with `│   └── fighter_overrides.py    ← MANUAL data fills...`), insert:

```
│   ├── reflection/
│   │   ├── __main__.py             ← CLI: python -m backend.reflection
│   │   ├── score.py                ← deterministic per-fight scoring (no LLM)
│   │   ├── reflect_runner.py       ← three Opus passes
│   │   ├── lesson_store.py         ← read/write lessons.json + regen lessons.md
│   │   ├── outcome_scraper.py      ← ufcstats results
│   │   ├── closing_line_scraper.py ← BFO closing lines per card
│   │   ├── detect_completed_events.py
│   │   └── prompts/{per_fight_reflection, card_meta_pass, lesson_merge}.md
```

And under `backend/cache/`, add:

```
│       ├── lessons.json            ← source of truth for prompt injection (LLM-owned)
│       ├── lessons.md              ← human-readable view (auto-regenerated)
│       ├── metrics_log.jsonl       ← one row per reflected event
│       └── scores/<event_key>.json ← deterministic per-event scoring
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "Document reflection pipeline in CLAUDE.md"
```

---

## Task 14: End-to-end dry-run on a real past event

**Files:** none modified.

- [ ] **Step 1: Find a candidate past event**

Run from project root:

```bash
python -m backend.reflection.detect_completed_events
```

Expected: at least one event in the past 7 days that matches our `analyses.json`. If the output is `[]`, set lookback higher temporarily for testing, e.g. edit `LOOKBACK_DAYS = 30` in `detect_completed_events.py`, rerun, and revert after the test.

- [ ] **Step 2: Run dry-run**

```bash
python -m backend.reflection --dry-run 2>&1 | tee /tmp/reflect-dry-run.log
```

Expected:
- Logs show: "scraping outcomes", "scraping closing lines", "scoring fights", per-fight rollup numbers, "running per-fight reflection (Opus)", etc.
- Final line: "reflection done" with no traceback.
- "=== Reflection delta ===" block prints near the end.
- NO new files written (dry-run).

- [ ] **Step 3: Inspect the would-be lessons**

The dry-run prints the delta summary but doesn't write files. To inspect the proposed lessons content, temporarily run WITHOUT --dry-run on a single past event to see the actual `lessons.json` output, then `git restore` the changes if they're not what you want:

```bash
python -m backend.reflection --event-key "<some past event_key>"
# Inspect:
cat backend/cache/lessons.json
cat backend/cache/lessons.md
# If results look bad:
git restore --staged backend/cache/lessons.json backend/cache/lessons.md backend/cache/metrics_log.jsonl
git checkout -- backend/cache/lessons.json backend/cache/lessons.md backend/cache/metrics_log.jsonl
rm -f backend/cache/scores/*.json
```

If results look reasonable (findings are concrete, agents are real, no hallucinated quotes), proceed to GHA verification.

- [ ] **Step 4: Trigger via GHA workflow_dispatch**

```bash
gh workflow run reflect.yml --repo zacharytroberts03-ctrl/ufc-11 -f dry_run=true
```

Then watch:

```bash
gh run watch --repo zacharytroberts03-ctrl/ufc-11 --exit-status
```

Expected: workflow completes successfully (exit 0). Inspect the log for any errors. If dry-run is clean, run again with `dry_run=false` to do the real commit.

---

## Task 15: Final commit + verification

**Files:** none — verification only.

- [ ] **Step 1: Verify all tests pass**

```bash
pytest backend/reflection/tests/ -v
```

Expected: all tests across `test_score.py`, `test_lesson_store.py`, `test_inject_lessons.py` PASS.

- [ ] **Step 2: Verify the spec's acceptance criteria are met**

Read the "Acceptance criteria" section of the design spec ([docs/superpowers/specs/2026-05-11-post-event-reflection-design.md](../specs/2026-05-11-post-event-reflection-design.md)) and tick each item:

- [ ] `.github/workflows/reflect.yml` ran successfully end-to-end (Task 14 step 4)
- [ ] `lessons.json` and `lessons.md` exist with at least the empty schema (Task 3 step 5)
- [ ] At least one `scores/<event_key>.json` exists if we've reflected on a real event
- [ ] A subsequent refresh-card.yml run loads lessons.json without error (verify by manually triggering refresh-card or waiting for Wed cron)
- [ ] All unit tests pass (Step 1 above)
- [ ] CLAUDE.md has the Reflection pipeline section and don't-do entry (Task 13)

- [ ] **Step 3: Push everything**

```bash
git push origin master
```

Expected: clean push, no conflicts.

- [ ] **Step 4: Final status**

The reflection system is shipped when:
- Sunday cron has fired at least once successfully
- At least one real event has been reflected on with reasonable findings
- Future refresh-card runs continue to succeed (lessons injection doesn't break anything)

Monitor the first 2-3 reflection cycles closely; expect early `watchlist` entries to dominate (low confidence on a single event) and the first `lessons[]` promotions to appear after 3-4 events of recurring patterns.
