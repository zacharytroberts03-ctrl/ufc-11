"""Load specialist agent files, invoke Claude per agent, parse the
{JSON + narrative} response. Per fight, fans out 20 calls (10 agents × 2
fighters as primary) in parallel.

Agent files live in `ufc-11/UFC agents/{offense,defense}/*.agent.md` per
the framework defined in that folder's README.md.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
import yaml

from pathlib import Path
from reflection.lesson_store import load_lessons, lessons_for_agent

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

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))
AGENTS_DIR = os.path.join(PROJECT_DIR, "UFC agents")

# Map README's `model: opus` / `model: sonnet` keywords to real model IDs.
MODEL_MAP = {
    "opus": "claude-opus-4-7",
    "sonnet": "claude-sonnet-4-6",
}
DEFAULT_OPUS = "claude-opus-4-7"
DEFAULT_SONNET = "claude-sonnet-4-6"

REQUIRED_REPORT_FIELDS = (
    "agent",
    "fighter",
    "rating_1_to_10",
    "sub_ratings",
    "strengths",
    "weaknesses",
    "signature_techniques",
    "effective_vs_archetypes",
    "vulnerable_to_archetypes",
    "recent_trend",
    "trend_evidence",
    "cardio_factor",
    "durability_factor",
    "key_stats_cited",
    "confidence",
)


def list_agent_paths() -> list[str]:
    """All 10 agent file paths (5 offense + 5 defense)."""
    paths = sorted(
        glob.glob(os.path.join(AGENTS_DIR, "offense", "*.agent.md"))
        + glob.glob(os.path.join(AGENTS_DIR, "defense", "*.agent.md"))
    )
    if len(paths) != 10:
        print(
            f"WARNING: expected 10 agent files in {AGENTS_DIR}, found {len(paths)}",
            file=sys.stderr,
        )
    return paths


def load_agent(path: str) -> tuple[dict, str, str]:
    """Parse YAML frontmatter and body. Returns (frontmatter, system_prompt, agent_name)."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    parts = re.split(r"^---\s*$", raw, maxsplit=2, flags=re.M)
    if len(parts) < 3:
        raise ValueError(f"Agent file {path} missing frontmatter delimiters")
    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    agent_name = frontmatter.get("name") or os.path.splitext(os.path.basename(path))[0].replace(".agent", "")
    return frontmatter, body, agent_name


def parse_response(text: str) -> dict:
    """Extract the JSON block + narrative from an agent response.
    Agents emit one ```json``` fenced block followed by 200-400 word narrative."""
    json_match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if not json_match:
        # Fallback: try to find first {...} block
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not brace_match:
            raise ValueError("No JSON block found in agent response")
        report = json.loads(brace_match.group(0))
        narrative = text[brace_match.end():].strip()
    else:
        report = json.loads(json_match.group(1))
        narrative = text[json_match.end():].strip()

    return {"report": report, "narrative": narrative, "raw": text}


def validate_report(parsed: dict, expected_agent: str) -> list[str]:
    """Return list of issues (empty = valid). Non-fatal — missing fields just
    flag low confidence in the synthesizer."""
    issues = []
    report = parsed.get("report", {})
    for field in REQUIRED_REPORT_FIELDS:
        if field not in report:
            issues.append(f"missing field: {field}")
    # Agent name is cosmetic — models sometimes emit the human-readable title
    # ("UFC Striking Offense Analyst") instead of the ID. We know which agent
    # this is from the file we invoked; the field is for reader clarity only.
    rating = report.get("rating_1_to_10")
    if rating is not None and not (isinstance(rating, int) and 1 <= rating <= 10):
        issues.append(f"rating_1_to_10 out of range: {rating!r}")
    return issues


# Schema reminder appended to every user payload. Sonnet (and even Opus) tend
# to drift toward inventing fields named after the agent's "analysis framework"
# lenses (e.g. "output_trend" instead of "recent_trend"). Reinforcing the
# exact schema at the call site prevents that without modifying the framework
# agent files.
_SCHEMA_REMINDER = """
Emit your report as ONE fenced ```json``` block followed by the 200-400 word markdown narrative. The JSON MUST use EXACTLY these top-level field names — no additions, no renames, no nesting beyond what is shown:

{
  "agent": "<agent-name-from-frontmatter>",
  "fighter": "<primary fighter name>",
  "opponent": <opponent name or null>,
  "rating_1_to_10": <integer 1-10>,
  "sub_ratings": {<the keys this agent's spec defines>},
  "strengths": [<3-5 short sentences>],
  "weaknesses": [<2-4 short sentences>],
  "signature_techniques": [<3-6 specific techniques>],
  "effective_vs_archetypes": [{"archetype": "<name>", "why": "<reason>"}],
  "vulnerable_to_archetypes": [{"archetype": "<name>", "why": "<reason>"}],
  "matchup_notes_vs_opponent": {"opponent_archetype": "...", "exploitable": [...], "must_avoid": [...], "x_factors": [...]} OR null,
  "recent_trend": "improving" | "declining" | "stable",
  "trend_evidence": "<one paragraph citing recent fights>",
  "cardio_factor": "<round-by-round assessment>",
  "durability_factor": "<chin/damage tolerance>",
  "camp_and_coaching_notes": "<text or 'unknown'>",
  "key_stats_cited": [{"stat": "...", "value": ..., "source": "..."}],
  "confidence": "high" | "medium" | "low",
  "data_caveats": [<empty array if confidence=high>]
}

Do NOT invent additional top-level fields like `archetype_primary`, `output_trend`, `power_assessment`, etc. — fold those observations into the narrative.
"""


def _build_user_payload(primary: str, opponent: str | None, dossier: dict, opponent_dossier: dict | None) -> str:
    payload = {"primary_fighter": primary, "dossier": dossier}
    if opponent:
        payload["opponent"] = opponent
    if opponent_dossier:
        payload["opponent_dossier"] = opponent_dossier
    return json.dumps(payload, ensure_ascii=False) + "\n\n---\n" + _SCHEMA_REMINDER


def run_one_agent(
    agent_path: str,
    primary: str,
    opponent: str | None,
    dossier: dict,
    opponent_dossier: dict | None,
    model: str,
    client: anthropic.Anthropic,
    max_tokens: int = 4096,
    temperature: float = 0.4,
) -> dict:
    """Invoke a single agent and return {report, narrative, raw, issues, agent_name}."""
    frontmatter, system_prompt, agent_name = load_agent(agent_path)
    system_prompt = _inject_lessons(system_prompt, agent_name)
    user_text = _build_user_payload(primary, opponent, dossier, opponent_dossier)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_text}],
    }
    # Opus 4.7+ rejects user-set temperature; let it use its default. Sonnet
    # still accepts the 0.4 setting that the framework recommends.
    if not model.startswith("claude-opus-4-7"):
        kwargs["temperature"] = temperature
    message = client.messages.create(**kwargs)
    text = message.content[0].text

    parsed = parse_response(text)
    parsed["agent_name"] = agent_name
    parsed["issues"] = validate_report(parsed, agent_name)
    parsed["model"] = model
    return parsed


def run_all_agents_for_fight(
    f1_dossier: dict,
    f2_dossier: dict,
    model: str,
    client: anthropic.Anthropic | None = None,
    cache=None,
    max_workers: int = 10,
) -> dict:
    """Fan out 20 agent calls (10 agents × 2 fighters as primary). Returns
    {fighter_name: {agent_name: parsed_report}}.

    If `cache` is provided, opportunistically skips API calls for cached
    (fighter, agent, opponent, last_fight_date) tuples."""
    # 5-min per-request timeout prevents a single hung HTTP call from blocking
    # the whole ThreadPoolExecutor — the bug that froze the 2026-05-10 catch-up
    # run mid-fight and left the site stale for 5 days.
    client = client or anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""), timeout=300.0)
    agent_paths = list_agent_paths()
    f1, f2 = f1_dossier["name"], f2_dossier["name"]

    tasks = []
    for ap in agent_paths:
        tasks.append(("f1", ap, f1, f2, f1_dossier, f2_dossier))
        tasks.append(("f2", ap, f2, f1, f2_dossier, f1_dossier))

    results: dict[str, dict[str, dict]] = {f1: {}, f2: {}}
    cache_hits = 0

    pending = []
    for side, ap, primary, opponent, dossier, opp_dossier in tasks:
        agent_name = os.path.splitext(os.path.basename(ap))[0].replace(".agent", "")
        if cache is not None:
            cached = cache.get(primary, agent_name, opponent, dossier.get("last_fight_date"))
            if cached is not None:
                results[primary][agent_name] = cached
                cache_hits += 1
                continue
        pending.append((side, ap, primary, opponent, dossier, opp_dossier, agent_name))

    print(
        f"  agents: {cache_hits} cache hit, {len(pending)} to fetch ({model})",
        flush=True,
    )

    if pending:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {
                ex.submit(
                    run_one_agent, ap, primary, opponent, dossier, opp_dossier, model, client
                ): (primary, agent_name)
                for side, ap, primary, opponent, dossier, opp_dossier, agent_name in pending
            }
            for future in as_completed(futures):
                primary, agent_name = futures[future]
                try:
                    parsed = future.result()
                    results[primary][agent_name] = parsed
                    if cache is not None:
                        cache.put(
                            primary,
                            agent_name,
                            results[primary][agent_name].get("report", {}).get("opponent"),
                            (f1_dossier if primary == f1 else f2_dossier).get("last_fight_date"),
                            parsed,
                        )
                except Exception as e:
                    print(f"    agent {agent_name} for {primary} FAILED: {e!r}", file=sys.stderr)
                    results[primary][agent_name] = {
                        "error": repr(e),
                        "agent_name": agent_name,
                    }

    return results


def select_model_for_fight(section: str) -> str:
    """Per Option C: Opus for main-card fights, Sonnet for prelims."""
    return DEFAULT_OPUS if section == "main" else DEFAULT_SONNET
