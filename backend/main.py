"""
UFC 11 — FastAPI Backend
Wraps all analysis tools as REST endpoints.
Run with: uvicorn main:app --reload --port 8000
"""

import os
import sys
import urllib.parse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from dotenv import load_dotenv

# ── Load .env from backend directory ─────────────────────────────────────────
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ── Add local tools to Python path ───────────────────────────────────────────
_BASE = os.path.dirname(__file__)
sys.path.insert(0, _BASE)
sys.path.insert(0, os.path.join(_BASE, "tools"))

# ── Imports ───────────────────────────────────────────────────────────────────
from scrape_ufc_card import scrape_upcoming_card
from scrape_ufc_fighter import scrape_fighter
from scrape_debut_fighter import scrape_debut_fighter
from scrape_odds import find_fight_odds
from hedge_calculator import summarize_hedge, annotate_odds_table
from analysis_runner import run_analysis
from cache import get_cached_analysis, fight_key, load_cache
import requests as _requests
import urllib.parse as _urlparse

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="UFC Fight Analyzer API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# ── Helper: fighter image lookup ──────────────────────────────────────────────

FRONTEND_URL = "https://frontend-rouge-mu-86.vercel.app"


def get_fighter_photo_url(name: str) -> str | None:
    slug = name.replace(" ", "_")
    return f"{FRONTEND_URL}/fighter_photos/{slug}.jpg"



# ── Pydantic models ───────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    f1: str
    f2: str
    total_stake: float = 100.0
    event_context: dict = {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/card")
def get_card():
    """Scrape the upcoming UFC card. Returns event info + fights list."""
    try:
        card = scrape_upcoming_card()

        if "fights" in card and "main_card" not in card:
            main_card = []
            prelims = []
            for fight in card.pop("fights", []):
                section = fight.get("section", "")
                if section == "main":
                    main_card.append(fight)
                else:
                    prelims.append(fight)
            card["main_card"] = main_card
            card["prelims"] = prelims

        for section in ("main_card", "prelims"):
            for fight in card.get(section, []):
                fight["f1_img"] = get_fighter_photo_url(fight["fighter1"])
                fight["f2_img"] = get_fighter_photo_url(fight["fighter2"])
        return card
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fighter/{name}")
def get_fighter(name: str):
    """Get fighter stats. Falls back to debut scraper if not found in UFC stats."""
    decoded = urllib.parse.unquote(name)
    try:
        try:
            data = scrape_fighter(decoded)
        except (ValueError, SystemExit):
            data = scrape_debut_fighter(decoded)
        data["photo_url"] = get_fighter_photo_url(decoded)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/odds/{f1}/{f2}")
def get_odds(f1: str, f2: str):
    """Get live odds for a matchup across sportsbooks."""
    f1d = urllib.parse.unquote(f1)
    f2d = urllib.parse.unquote(f2)
    try:
        odds = find_fight_odds(f1d, f2d)
        if odds is None:
            return {"available": False}
        hedge = summarize_hedge(f1d, f2d, odds, total_stake=100.0)
        annotated = annotate_odds_table(odds["books"], odds.get("fighter1", f1d), odds.get("fighter2", f2d))
        return {
            "available": True,
            "fighter1": odds.get("fighter1", f1d),
            "fighter2": odds.get("fighter2", f2d),
            "books": annotated,
            "best_f1": odds["best_f1"],
            "best_f2": odds["best_f2"],
            "hedge": hedge,
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


@app.get("/api/analysis/{key}")
def get_analysis_cached(key: str):
    """Return a cached fight analysis by fight key."""
    cache = load_cache()
    result = cache.get("fights", {}).get(key)
    if result is None:
        raise HTTPException(status_code=404, detail="No cached analysis found")
    return result


@app.get("/api/analysis/lookup/{f1}/{f2}")
def lookup_analysis(f1: str, f2: str):
    """Look up cached analysis by fighter names."""
    f1d = urllib.parse.unquote(f1)
    f2d = urllib.parse.unquote(f2)
    result = get_cached_analysis(f1d, f2d)
    if result is None:
        raise HTTPException(status_code=404, detail="No cached analysis found")
    return result


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """Run the full AI analysis pipeline. May take 30-60 seconds."""
    try:
        result = run_analysis(
            f1_name=req.f1,
            f2_name=req.f2,
            total_stake=req.total_stake,
            event_context=req.event_context or {},
        )
        result["f1_img"] = get_fighter_photo_url(result.get("f1_name", req.f1))
        result["f2_img"] = get_fighter_photo_url(result.get("f2_name", req.f2))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
