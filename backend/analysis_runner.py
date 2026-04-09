"""Headless analysis pipeline — no Streamlit imports.

Used by both app.py (live, cache hit) and scripts/refresh_cache.py (cron).
"""

import os
import re
import sys
import datetime

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

from scrape_ufc_fighter import scrape_fighter
from scrape_debut_fighter import scrape_debut_fighter
from scrape_odds import find_fight_odds
from hedge_calculator import summarize_hedge
import anthropic

# Optional new data sources — all wrapped in try/except at call sites
try:
    from scrape_bestfightodds import scrape_line_movement
except Exception:
    scrape_line_movement = None
try:
    from scrape_tapology import scrape_tapology_intangibles
except Exception:
    scrape_tapology_intangibles = None
try:
    from altitude_lookup import lookup_altitude
except Exception:
    lookup_altitude = None


# ── Derived-field helpers ─────────────────────────────────────────────────────

def _parse_dob(dob_str: str) -> datetime.date | None:
    """Parse a DOB string from ufcstats ('Aug 19, 1987') or Tapology variants."""
    if not dob_str or dob_str in ("N/A", "--"):
        return None
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.datetime.strptime(dob_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _compute_age(dob_str: str) -> int | None:
    dob = _parse_dob(dob_str)
    if not dob:
        return None
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _parse_fight_date(date_str: str) -> datetime.date | None:
    """Parse fight history date strings ('Apr. 12, 2024' or 'April 12, 2024')."""
    if not date_str or date_str == "N/A":
        return None
    cleaned = date_str.replace(".", "")
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.datetime.strptime(cleaned.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _compute_layoff_days(fight_history: list[dict]) -> int | None:
    """Days since the most recent fight in history."""
    for f in fight_history:
        d = _parse_fight_date(f.get("date", ""))
        if d:
            return (datetime.date.today() - d).days
    return None


def _parse_reach_inches(reach_str: str) -> float | None:
    """Parse '74.0\"' → 74.0"""
    if not reach_str or reach_str == "N/A":
        return None
    m = re.search(r'(\d+(?:\.\d+)?)', reach_str)
    return float(m.group(1)) if m else None


_RULES_PATH = os.path.join(BASE_DIR, "rules", "BETTING_AI_RULES.md")
with open(_RULES_PATH, "r", encoding="utf-8") as f:
    BETTING_AI_RULES = f.read()


SYSTEM_PROMPT = f"""You are an expert UFC analyst and sports betting strategist with deep knowledge of mixed martial arts, fighter styles, matchup dynamics, and line value identification.

{BETTING_AI_RULES}

When analyzing a matchup:
1. Follow all rules in the FIGHT ANALYSIS RULES section above
2. Use the exact output format defined in OUTPUT FORMAT RULES
3. Always include the BETTING section as defined in BETTING RECOMMENDATION RULES
4. Be specific -- cite statistics, not adjectives
5. If stats show N/A (UFC debut), acknowledge the gap and analyze from available data only

OUTPUT CLEANLINESS RULES (non-negotiable):
NEVER include any of the following in your written output:
- Data Tier labels (HIGH / MEDIUM / LOW)
- References to rules, sections, or matrices (e.g. "Section 5.1", "per the matrix", "Rule 3.7")
- Edge percentage calculations or formulas (e.g. "+7.4% edge", "35% assessed vs. 27.6% market true prob")
- Confidence cap language (e.g. "capped at 55% after market move penalty")
- Market cent movements (e.g. "550-cent sharp move", "200-cent line move")
- Meta-commentary about your process (e.g. "Fade alert: Initial read was...", "Flip condition:")
- Internal system flags as labels (e.g. write "he has been knocked out twice in his last three fights" not "CHIN CRACKED")
- Archetype codes as standalone labels (e.g. don't write "Volume Striker vs. Counter-Striker" — describe the style in plain English instead)

Write as a knowledgeable analyst speaking to a fan, not as a rule-following system printing a report.
"""


def format_fighter_block(f: dict) -> str:
    r = f["record"]
    s = f["striking"]
    g = f["grappling"]
    wm = f["win_methods"]
    wm_note = wm.get("note", "")
    is_debut = f.get("ufc_debut", False)
    debut_source = f.get("debut_source", "Tapology")

    age = _compute_age(f.get("dob", ""))
    age_str = f"{age}" if age is not None else "N/A"
    layoff_days = _compute_layoff_days(f.get("fight_history", []))
    layoff_str = f"{layoff_days} days" if layoff_days is not None else "N/A"

    stance = f.get("stance", "")
    southpaw_tag = " (SOUTHPAW)" if stance and "southpaw" in stance.lower() else ""

    # Last-3 splits block
    last_3 = f.get("last_3_splits", [])
    if last_3:
        split_lines = []
        for sp in last_3:
            split_lines.append(
                f"  {sp.get('date','?')} vs {sp.get('opponent','?')} "
                f"({sp.get('result','?')} by {sp.get('method','?')}): "
                f"SLpM {sp.get('slpm','?')}, Str.Acc {sp.get('str_acc_pct','?')}%, "
                f"TD/15 {sp.get('td_per_15','?')}, Sub/15 {sp.get('sub_per_15','?')}"
            )
        last_3_block = "Last-3 per-fight splits (computed from fight detail pages):\n" + "\n".join(split_lines)
    else:
        last_3_block = "Last-3 per-fight splits: NOT AVAILABLE — apply Rule 3.7 (insufficient sample for trend)."

    # Tapology-sourced intangibles, if any
    intangibles = f.get("intangibles", {}) or {}
    intangibles_lines = []
    if intangibles.get("camp"):
        intangibles_lines.append(f"  Camp: {intangibles['camp']}")
    if intangibles.get("short_notice") is True:
        intangibles_lines.append(f"  SHORT NOTICE FLAG: True ({intangibles.get('notice_days','?')} days)")
    if intangibles.get("weight_miss_history"):
        intangibles_lines.append(f"  Weight-miss history: {intangibles['weight_miss_history']}")
    if intangibles_lines:
        intangibles_block = "Intangibles (Tapology):\n" + "\n".join(intangibles_lines)
    else:
        intangibles_block = "Intangibles (Tapology): NOT AVAILABLE"

    history_lines = []
    for fight in f["fight_history"]:
        line = f"  {fight['result']} vs {fight['opponent']} -- {fight['method']}"
        if fight.get("promotion"):
            line += f" [{fight['promotion']}]"
        if fight.get("round") and fight["round"] != "N/A":
            line += f", R{fight['round']}"
        if fight.get("time") and fight["time"] != "N/A":
            line += f" ({fight['time']})"
        history_lines.append(line)

    history_text = "\n".join(history_lines) if history_lines else "  (No fight history parsed)"

    debut_header = ""
    stats_note = ""
    if is_debut:
        debut_header = f"  *** UFC DEBUT -- stats sourced from {debut_source} (pre-UFC career) ***\n"
        stats_note = (
            "\nNOTE: UFC per-minute striking/grappling averages are not available for this fighter "
            "as they have no UFC fights. Analyze their style based on fight history and win methods only."
        )

    return f"""=== {f['name'].upper()}{southpaw_tag} ===
{debut_header}Record: {r['wins']}-{r['losses']}-{r['draws']}
Age: {age_str} | Layoff since last fight: {layoff_str}
Height: {f['height']} | Weight: {f['weight']} | Reach: {f['reach']} | Stance: {f['stance']}

Striking (CAREER averages -- UFC only):
  {s['slpm']} sig. strikes landed/min | {s['sapm']} absorbed/min
  {s['str_acc']} striking accuracy | {s['str_def']} strike defense

Grappling (CAREER averages -- UFC only):
  {g['td_avg']} takedowns/15min | {g['td_acc']} TD accuracy | {g['td_def']} TD defense
  {g['sub_avg']} submission attempts/15min

Win methods {wm_note}: {wm['ko']} KO/TKO | {wm['sub']} Submissions | {wm['dec']} Decisions

{last_3_block}

{intangibles_block}

Recent fight history (most recent first):
{history_text}{stats_note}"""


def format_matchup_context_block(f1: dict, f2: dict, context: dict) -> str:
    """Render the MATCHUP CONTEXT block — venue/altitude/lines/diffs."""
    f1_reach = _parse_reach_inches(f1.get("reach", ""))
    f2_reach = _parse_reach_inches(f2.get("reach", ""))
    if f1_reach is not None and f2_reach is not None:
        reach_diff = f1_reach - f2_reach
        reach_line = (
            f"Reach differential: {f1['name']} {f1_reach}\" vs {f2['name']} {f2_reach}\" "
            f"(delta: {reach_diff:+.1f}\")"
        )
    else:
        reach_line = "Reach differential: N/A"

    age1 = _compute_age(f1.get("dob", ""))
    age2 = _compute_age(f2.get("dob", ""))
    if age1 is not None and age2 is not None:
        age_line = f"Age differential: {f1['name']} {age1} vs {f2['name']} {age2} (delta: {age1 - age2:+d})"
    else:
        age_line = "Age differential: N/A"

    venue = context.get("venue", "Unknown")
    altitude = context.get("altitude_ft")
    altitude_line = f"Venue: {venue} | Altitude: {altitude} ft" if altitude else f"Venue: {venue} | Altitude: unknown"

    sched = context.get("scheduled_rounds", "Unknown")
    main_event = "MAIN EVENT" if context.get("is_main_event") else "Undercard"
    title = "TITLE FIGHT" if context.get("is_title_fight") else ""
    fight_type_line = f"Format: {sched} rounds | {main_event} {title}".strip()

    line_movement = context.get("line_movement") or {}
    if line_movement:
        lm_lines = []
        for fname in (f1["name"], f2["name"]):
            entry = line_movement.get(fname, {})
            opening = entry.get("opening", "?")
            current = entry.get("current", "?")
            direction = entry.get("direction", "?")
            lm_lines.append(f"  {fname}: open {opening} → current {current} ({direction})")
        rlm = line_movement.get("reverse_line_movement", False)
        public = line_movement.get("public_pct", {})
        if public:
            lm_lines.append(f"  Public %: {public}")
        lm_lines.append(f"  Reverse line movement (RLM): {'YES' if rlm else 'NO'}")
        line_block = "Line movement (BestFightOdds):\n" + "\n".join(lm_lines)
    else:
        line_block = "Line movement: NOT AVAILABLE — apply Rule 10.1 (skip Section 10)."

    return f"""=== MATCHUP CONTEXT ===
{altitude_line}
{fight_type_line}
{reach_line}
{age_line}

{line_block}"""


def build_prompt(f1: dict, f2: dict, context: dict | None = None) -> str:
    context = context or {}
    return f"""{format_matchup_context_block(f1, f2, context)}

{format_fighter_block(f1)}

{format_fighter_block(f2)}

---

Produce the following analysis in this EXACT format, including the HTML comment markers exactly as shown:

<!--F1_PROFILE-->
## {f1['name']} -- Style & Profile
[Write 4-6 concise bullet points. Each bullet is one sharp observation about this fighter: their style, best weapon, tendencies, behavior under pressure, or notable patterns from their fight history. Write naturally, like an analyst talking to a fan. Stats can back up a point but should support the insight, not replace it. No system labels, no jargon, no filler.]
<!--END-->

<!--F2_PROFILE-->
## {f2['name']} -- Style & Profile
[Same structure as above -- 4-6 concise bullet points written in plain analyst language.]
<!--END-->

<!--HEAD2HEAD-->
## Head-to-Head: Strengths & Weaknesses
[2-3 paragraphs breaking down how these two styles match up. Where does each fighter have the edge? What are the key exchanges that will decide this fight? Keep it direct and readable -- no system labels or rule references.]
<!--END-->

<!--ENDINGS-->
## Most Likely Fight Endings

Generate between 3 and 5 outcomes, ranked from most to least likely. Use 3 when the matchup has a clear direction and limited realistic scenarios. Use 4 or 5 when there are multiple genuine paths to victory for either fighter.

**#1 -- [Specific description, e.g., "Jon Jones wins by TKO, Round 3"]**
Likelihood: High
Why: [2-3 sentences of plain-English reasoning]

**#2 -- [Specific description]**
Likelihood: Moderate
Why: [2-3 sentences of plain-English reasoning]

**#3 -- [Specific description]**
Likelihood: Low
Why: [2-3 sentences of plain-English reasoning]

[Add #4 and #5 only if the matchup genuinely warrants additional scenarios. Use Likelihood: Low for these.]
<!--END-->

<!--BETTING-->
Include the full betting recommendation as defined in the BETTING RECOMMENDATION RULES in the system prompt. Use the exact structure specified there. Do NOT include edge percentages, confidence cap language, market cent movements, or meta-commentary about your process -- just the pick, the reasoning, the stake, and the hedge verdict in plain English.
<!--END-->"""


def parse_analysis_sections(text: str) -> dict:
    sections = {}
    pattern = r"<!--(\w+)-->(.*?)<!--END-->"
    for match in re.finditer(pattern, text, re.DOTALL):
        key = match.group(1).lower()
        sections[key] = match.group(2).strip()
    return sections


def get_analysis(f1: dict, f2: dict, context: dict | None = None) -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    prompt = build_prompt(f1, f2, context)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _scrape_one(name: str) -> dict:
    try:
        return scrape_fighter(name)
    except (ValueError, SystemExit):
        return scrape_debut_fighter(name)


def run_analysis(
    f1_name: str,
    f2_name: str,
    total_stake: float = 100.0,
    event_context: dict | None = None,
) -> dict:
    """Run the full pipeline headlessly. Returns a JSON-serializable dict."""
    f1_data = _scrape_one(f1_name)
    f2_data = _scrape_one(f2_name)

    # Best-effort Tapology intangibles per fighter
    if scrape_tapology_intangibles is not None:
        for fdata in (f1_data, f2_data):
            try:
                fdata["intangibles"] = scrape_tapology_intangibles(fdata["name"]) or {}
            except Exception:
                fdata["intangibles"] = {}

    odds_data = None
    hedge_summary = None
    try:
        odds_data = find_fight_odds(f1_data["name"], f2_data["name"])
        if odds_data:
            hedge_summary = summarize_hedge(
                f1_data["name"], f2_data["name"], odds_data, total_stake
            )
    except Exception:
        pass

    # Best-effort line movement from BestFightOdds
    line_movement = None
    if scrape_line_movement is not None:
        try:
            line_movement = scrape_line_movement(f1_data["name"], f2_data["name"])
        except Exception:
            line_movement = None

    # Build matchup context dict for the prompt
    venue = (event_context or {}).get("location", "Unknown")
    altitude = None
    if lookup_altitude is not None:
        try:
            altitude = lookup_altitude(venue)
        except Exception:
            altitude = None

    matchup_context = {
        "venue": venue,
        "altitude_ft": altitude,
        "scheduled_rounds": (event_context or {}).get("scheduled_rounds", "Unknown"),
        "is_main_event": (event_context or {}).get("is_main_event", False),
        "is_title_fight": (event_context or {}).get("is_title_fight", False),
        "line_movement": line_movement,
    }

    raw_analysis = get_analysis(f1_data, f2_data, matchup_context)
    analysis_sections = parse_analysis_sections(raw_analysis)

    return {
        "f1_name": f1_data["name"],
        "f2_name": f2_data["name"],
        "f1_data": f1_data,
        "f2_data": f2_data,
        "odds_data": odds_data,
        "hedge_summary": hedge_summary,
        "analysis_sections": analysis_sections,
        "raw_analysis": raw_analysis,
        "total_stake": total_stake,
        "matchup_context": matchup_context,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
