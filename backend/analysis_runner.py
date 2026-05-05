"""Headless analysis pipeline — agent-based.

Per fight:
  1. Scrape both fighters' dossiers (UFC stats, falling back to Tapology / debut).
  2. Best-effort enrichment: live odds, hedge calc, line movement, tapology
     intangibles, venue altitude.
  3. Fan out 20 specialist Claude calls (10 per fighter) in parallel.
  4. Run a synthesis pass that produces the markdown sections the frontend
     already reads, plus a structured `bets` object and the domain-advantage
     table backing the picks.

Used by both app.py (live, cache hit) and scripts/refresh_cache.py (cron).
"""

import datetime
import os
import re
import sys

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))
sys.path.insert(0, BASE_DIR)

import anthropic

from scrape_ufc_fighter import scrape_fighter
from scrape_debut_fighter import scrape_debut_fighter
from scrape_odds import find_fight_odds
from hedge_calculator import summarize_hedge

from agents.dossier import build_dossier
from agents.agent_runner import (
    run_all_agents_for_fight,
    select_model_for_fight,
)
from agents.agent_cache import AgentReportCache
from agents.synthesizer import synthesize
from agents.fighter_overrides import apply_intangibles_overrides

# Optional new data sources — wrapped in try/except at call sites
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


# ── Date / number helpers (still used by app.py and external callers) ─────────

def _parse_dob(dob_str: str) -> datetime.date | None:
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
    for f in fight_history:
        d = _parse_fight_date(f.get("date", ""))
        if d:
            return (datetime.date.today() - d).days
    return None


def _parse_reach_inches(reach_str: str) -> float | None:
    if not reach_str or reach_str == "N/A":
        return None
    m = re.search(r'(\d+(?:\.\d+)?)', reach_str)
    return float(m.group(1)) if m else None


def _scrape_one(name: str) -> dict:
    try:
        return scrape_fighter(name)
    except (ValueError, SystemExit):
        return scrape_debut_fighter(name)


# ── Module-level shared caches ────────────────────────────────────────────────
# Loaded once per process; saved after each run_analysis() call so partial
# progress survives crashes mid-card.

_AGENT_CACHE: AgentReportCache | None = None


def _get_agent_cache() -> AgentReportCache:
    global _AGENT_CACHE
    if _AGENT_CACHE is None:
        _AGENT_CACHE = AgentReportCache()
    return _AGENT_CACHE


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_analysis(
    f1_name: str,
    f2_name: str,
    total_stake: float = 100.0,
    event_context: dict | None = None,
) -> dict:
    """Run the full pipeline headlessly. Returns a JSON-serializable dict.

    Output shape (top-level keys):
      f1_name, f2_name, f1_data, f2_data           — raw scrape outputs
      odds_data, hedge_summary                      — best-effort odds
      analysis_sections                             — markdown for frontend
      raw_analysis                                  — synthesizer raw text
      bets                                          — structured bets JSON
      domain_advantages                             — deterministic advantage table
      specialist_reports                            — {f1: {agent: {...}}, f2: {...}}
      total_stake, matchup_context, generated_at
    """
    event_context = event_context or {}

    f1_data = _scrape_one(f1_name)
    f2_data = _scrape_one(f2_name)

    # Best-effort tapology intangibles, then merge in manual overrides
    for fdata in (f1_data, f2_data):
        scraped: dict = {}
        if scrape_tapology_intangibles is not None:
            try:
                scraped = scrape_tapology_intangibles(fdata["name"]) or {}
            except Exception:
                scraped = {}
        fdata["intangibles"] = apply_intangibles_overrides(fdata["name"], scraped)

    # Best-effort live odds + hedge calc
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

    # Best-effort line movement
    line_movement = None
    if scrape_line_movement is not None:
        try:
            line_movement = scrape_line_movement(f1_data["name"], f2_data["name"])
        except Exception:
            line_movement = None

    # Venue / altitude
    venue = event_context.get("location", "Unknown")
    altitude = None
    if lookup_altitude is not None:
        try:
            altitude = lookup_altitude(venue)
        except Exception:
            altitude = None

    matchup_context = {
        "venue": venue,
        "altitude_ft": altitude,
        "scheduled_rounds": event_context.get("scheduled_rounds", "Unknown"),
        "is_main_event": event_context.get("is_main_event", False),
        "is_title_fight": event_context.get("is_title_fight", False),
        "section": event_context.get("section", "main" if event_context.get("is_main_event") else "prelim"),
        "line_movement": line_movement,
        "live_odds": odds_data,
    }

    # Build dossiers in the shape the agents expect
    f1_dossier = build_dossier(f1_data)
    f2_dossier = build_dossier(f2_data)

    # Pick model: Opus for main card, Sonnet for prelims
    model = select_model_for_fight(matchup_context["section"])

    # Fan out 20 specialist agent calls (parallel, cached)
    cache = _get_agent_cache()
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    specialist_reports = run_all_agents_for_fight(
        f1_dossier, f2_dossier, model=model, client=client, cache=cache
    )
    cache.save()

    # Synthesis pass — same model as specialists for consistency
    synthesis = synthesize(
        f1_dossier=f1_dossier,
        f2_dossier=f2_dossier,
        f1_reports=specialist_reports[f1_dossier["name"]],
        f2_reports=specialist_reports[f2_dossier["name"]],
        matchup_context=matchup_context,
        model=model,
        client=client,
    )

    return {
        "f1_name": f1_data["name"],
        "f2_name": f2_data["name"],
        "f1_data": f1_data,
        "f2_data": f2_data,
        "f1_dossier": f1_dossier,
        "f2_dossier": f2_dossier,
        "odds_data": odds_data,
        "hedge_summary": hedge_summary,
        "analysis_sections": synthesis["analysis_sections"],
        "bets": synthesis["bets"],
        "domain_advantages": synthesis["domain_advantages"],
        "specialist_reports": specialist_reports,
        "raw_analysis": synthesis["raw"],
        "aggregator_model": synthesis["aggregator_model"],
        "total_stake": total_stake,
        "matchup_context": matchup_context,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
