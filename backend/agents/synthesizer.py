"""Synthesis layer: turn 20 specialist agent reports into a fight prediction +
structured betting recommendations.

Two-stage:
  1. Deterministic domain-advantage table (computed from sub-ratings).
  2. LLM aggregator that reads the table + all 20 JSON reports + dossiers and
     emits the 5 markdown sections the frontend already renders, plus a
     structured `bets` object for future betting UI.
"""

from __future__ import annotations

import json
import os
import re

import anthropic

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


# Each pair: (offense_agent, defense_agent) within a single domain.
DOMAINS = [
    ("striking", "ufc-striking-offense", "ufc-striking-defense"),
    ("wrestling", "ufc-wrestling-offense", "ufc-wrestling-defense"),
    ("takedowns", "ufc-takedown-offense", "ufc-takedown-defense"),
    ("grappling", "ufc-grappling-offense", "ufc-grappling-defense"),
    ("submissions", "ufc-submission-offense", "ufc-submission-defense"),
]


def _safe_rating(reports: dict, agent_name: str) -> int | None:
    parsed = reports.get(agent_name) or {}
    report = parsed.get("report") or {}
    r = report.get("rating_1_to_10")
    return r if isinstance(r, int) and 1 <= r <= 10 else None


def compute_domain_advantages(f1_reports: dict, f2_reports: dict) -> dict:
    """Per domain, compute advantage as:
        (f1_offense - f2_defense) - (f2_offense - f1_defense)
    Positive = f1 wins the domain; negative = f2 wins. None = data missing.
    """
    out: dict[str, dict] = {}
    for domain, off_agent, def_agent in DOMAINS:
        f1_off = _safe_rating(f1_reports, off_agent)
        f2_def = _safe_rating(f2_reports, def_agent)
        f2_off = _safe_rating(f2_reports, off_agent)
        f1_def = _safe_rating(f1_reports, def_agent)

        f1_pressure = (f1_off - f2_def) if (f1_off is not None and f2_def is not None) else None
        f2_pressure = (f2_off - f1_def) if (f2_off is not None and f1_def is not None) else None

        if f1_pressure is None and f2_pressure is None:
            advantage = None
        else:
            advantage = (f1_pressure or 0) - (f2_pressure or 0)

        out[domain] = {
            "f1_offense": f1_off,
            "f2_defense": f2_def,
            "f2_offense": f2_off,
            "f1_defense": f1_def,
            "f1_pressure": f1_pressure,
            "f2_pressure": f2_pressure,
            "advantage": advantage,  # >0 favors f1, <0 favors f2
        }
    return out


def _strip_narrative(parsed: dict) -> dict:
    """Compact a parsed agent response down to just the structured fields the
    aggregator needs. Keeps tokens manageable."""
    if "error" in parsed:
        return {"error": parsed.get("error"), "agent": parsed.get("agent_name")}
    report = parsed.get("report", {})
    return {
        "agent": report.get("agent"),
        "fighter": report.get("fighter"),
        "opponent": report.get("opponent"),
        "rating_1_to_10": report.get("rating_1_to_10"),
        "sub_ratings": report.get("sub_ratings"),
        "strengths": report.get("strengths"),
        "weaknesses": report.get("weaknesses"),
        "signature_techniques": report.get("signature_techniques"),
        "effective_vs_archetypes": report.get("effective_vs_archetypes"),
        "vulnerable_to_archetypes": report.get("vulnerable_to_archetypes"),
        "matchup_notes_vs_opponent": report.get("matchup_notes_vs_opponent"),
        "recent_trend": report.get("recent_trend"),
        "trend_evidence": report.get("trend_evidence"),
        "cardio_factor": report.get("cardio_factor"),
        "durability_factor": report.get("durability_factor"),
        "key_stats_cited": report.get("key_stats_cited"),
        "confidence": report.get("confidence"),
        "data_caveats": report.get("data_caveats"),
    }


_RULES_PATH = os.path.join(BACKEND_DIR, "rules", "BETTING_AI_RULES.md")
try:
    with open(_RULES_PATH, "r", encoding="utf-8") as f:
        BETTING_AI_RULES = f.read()
except OSError:
    BETTING_AI_RULES = ""


SYNTHESIZER_SYSTEM = f"""You are the head betting analyst synthesizing 10 specialist scout reports per fighter into a single fight prediction and a betting recommendation.

You have:
- A deterministic DOMAIN ADVANTAGE TABLE (5 numbers) computed from agents' ratings.
- 20 specialist agent reports (10 per fighter) with structured ratings, strengths, weaknesses, archetype matchups, trend, cardio, durability, and matchup_notes_vs_opponent.
- Both fighters' dossiers and the matchup context (venue, altitude, format, live odds, line movement).

Your job is to produce:
1. Five markdown sections (delimited with HTML comment markers exactly as instructed) that read like an analyst speaking to a fan.
2. A structured `bets` JSON block with calibrated probabilities for moneyline, method-of-victory, distance, and rounds.

{BETTING_AI_RULES}

OUTPUT CLEANLINESS RULES (non-negotiable):
NEVER include any of the following in your written output:
- Data Tier labels (HIGH / MEDIUM / LOW)
- References to rules, sections, or matrices ("Section 5.1", "per the matrix", "Rule 3.7")
- Edge percentage calculations or formulas ("+7.4% edge")
- Confidence cap language ("capped at 55% after market move penalty")
- Market cent movements ("550-cent sharp move")
- Meta-commentary about your process ("Fade alert: Initial read was...")
- Internal system flags as labels (write "he has been knocked out twice" not "CHIN CRACKED")
- Archetype codes as standalone labels (describe the style in plain English)
- References to "agent reports" or "specialists" — synthesize the analysis as your own observations

Write as a knowledgeable analyst speaking to a fan, not as a rule-following system printing a report.
"""


def _build_user_payload(
    f1_dossier: dict,
    f2_dossier: dict,
    f1_reports: dict,
    f2_reports: dict,
    advantages: dict,
    matchup_context: dict,
) -> str:
    f1_compact = {a: _strip_narrative(p) for a, p in f1_reports.items()}
    f2_compact = {a: _strip_narrative(p) for a, p in f2_reports.items()}
    payload = {
        "f1_name": f1_dossier["name"],
        "f2_name": f2_dossier["name"],
        "f1_dossier": f1_dossier,
        "f2_dossier": f2_dossier,
        "domain_advantages": advantages,
        "f1_specialist_reports": f1_compact,
        "f2_specialist_reports": f2_compact,
        "matchup_context": matchup_context,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


_OUTPUT_INSTRUCTIONS = """Produce the analysis below. The HTML comment markers MUST appear exactly as shown — the frontend parses them.

<!--F1_PROFILE-->
## {f1_name} -- Style & Profile
[4-6 concise bullet points. Each bullet is one sharp observation about this fighter's style, best weapon, tendencies, behavior under pressure, or notable patterns. Synthesize from all 10 specialist views — striking, wrestling, takedowns, grappling, submissions, on both offense and defense. Plain analyst language.]
<!--END-->

<!--F2_PROFILE-->
## {f2_name} -- Style & Profile
[Same structure as above for {f2_name}.]
<!--END-->

<!--HEAD2HEAD-->
## Head-to-Head: Strengths & Weaknesses
[2-3 paragraphs. Open with which domain advantage(s) decide the fight, then map specific exchanges. Cite concrete examples from the specialists' matchup notes — e.g. footwork, range, top control, scrambles. Keep it readable.]
<!--END-->

<!--ENDINGS-->
## Most Likely Fight Endings

Generate 3 to 5 outcomes ranked from most to least likely. Use 3 when the matchup has a clear direction and limited realistic scenarios. Use 4 or 5 when there are multiple genuine paths to victory for either fighter.

**#1 -- [Specific description, e.g., "Jon Jones wins by TKO, Round 3"]**
Likelihood: High
Why: [2-3 sentences of plain-English reasoning grounded in the specialist analysis]

**#2 -- [Specific description]**
Likelihood: Moderate
Why: [2-3 sentences]

**#3 -- [Specific description]**
Likelihood: Low
Why: [2-3 sentences]

[Optional #4 and #5 only if the matchup warrants them. Use Likelihood: Low.]
<!--END-->

<!--BETTING-->
[Full betting recommendation per the BETTING RECOMMENDATION RULES in the system prompt. The pick, the reasoning, the stake, the hedge verdict — plain English. NO edge percentages, NO confidence cap language, NO market cent movements.]
<!--END-->

After all five markdown sections, emit a single fenced JSON block with structured probabilities. This is for the betting UI — distinct from the markdown above.

```json
{{
  "moneyline": {{
    "pick": "{f1_name} | {f2_name}",
    "win_prob": 0.0-1.0,
    "confidence": "high | medium | low",
    "key_thesis": "one sentence"
  }},
  "method": {{
    "ko_tko": 0.0-1.0,
    "submission": 0.0-1.0,
    "decision": 0.0-1.0
  }},
  "distance": {{
    "goes_to_decision": 0.0-1.0,
    "ends_inside_distance": 0.0-1.0
  }},
  "rounds": {{
    "ends_round_1": 0.0-1.0,
    "ends_round_2": 0.0-1.0,
    "ends_round_3": 0.0-1.0,
    "ends_round_4_or_later": 0.0-1.0
  }},
  "supporting_specialists": ["agent-name", "agent-name"],
  "domain_summary": {{
    "striking": "brief one-line who-wins-and-why",
    "wrestling": "...",
    "takedowns": "...",
    "grappling": "...",
    "submissions": "..."
  }}
}}
```

Method probabilities should sum to ~1.0 (small rounding OK). Round probabilities should sum to ~`ends_inside_distance` (the rest is decision)."""


def _parse_synthesizer_response(text: str) -> dict:
    """Extract the 5 HTML-comment-delimited markdown sections + the trailing
    JSON block."""
    sections = {}
    for match in re.finditer(r"<!--(\w+)-->(.*?)<!--END-->", text, re.DOTALL):
        key = match.group(1).lower()
        sections[key] = match.group(2).strip()

    bets = {}
    json_match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if json_match:
        try:
            bets = json.loads(json_match.group(1))
        except json.JSONDecodeError:
            bets = {"_parse_error": "invalid JSON in bets block", "raw": json_match.group(1)[:500]}

    return {"analysis_sections": sections, "bets": bets, "raw": text}


def synthesize(
    f1_dossier: dict,
    f2_dossier: dict,
    f1_reports: dict,
    f2_reports: dict,
    matchup_context: dict,
    model: str,
    client: anthropic.Anthropic | None = None,
    max_tokens: int = 8192,
) -> dict:
    """Run the aggregator. Returns a dict with analysis_sections, bets,
    domain_advantages, and the raw aggregator output."""
    advantages = compute_domain_advantages(f1_reports, f2_reports)
    client = client or anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""), timeout=300.0)

    user_payload = _build_user_payload(
        f1_dossier, f2_dossier, f1_reports, f2_reports, advantages, matchup_context
    )

    instructions = _OUTPUT_INSTRUCTIONS.format(
        f1_name=f1_dossier["name"], f2_name=f2_dossier["name"]
    )
    user_text = (
        f"DATA (JSON):\n{user_payload}\n\n---\n\nINSTRUCTIONS:\n{instructions}"
    )

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": SYNTHESIZER_SYSTEM,
        "messages": [{"role": "user", "content": user_text}],
    }
    if not model.startswith("claude-opus-4-7"):
        kwargs["temperature"] = 0.4
    message = client.messages.create(**kwargs)
    text = message.content[0].text
    parsed = _parse_synthesizer_response(text)
    parsed["domain_advantages"] = advantages
    parsed["aggregator_model"] = model
    return parsed
