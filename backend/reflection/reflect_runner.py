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
