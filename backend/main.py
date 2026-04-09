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
from fastapi.staticfiles import StaticFiles
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

# Serve local fighter photos if present
PHOTOS_DIR = os.path.join(_BASE, "fighter_photos")
if os.path.isdir(PHOTOS_DIR):
    app.mount("/fighter_photos", StaticFiles(directory=PHOTOS_DIR), name="fighter_photos")


# ── Helper: fighter image lookup ──────────────────────────────────────────────

_PHOTO_INDEX: dict[str, str] | None = None


def _photo_index() -> dict[str, str]:
    global _PHOTO_INDEX
    if _PHOTO_INDEX is None:
        index: dict[str, str] = {}
        if os.path.isdir(PHOTOS_DIR):
            for fname in os.listdir(PHOTOS_DIR):
                stem, ext = os.path.splitext(fname)
                if ext.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                    index[stem.lower()] = fname
        _PHOTO_INDEX = index
    return _PHOTO_INDEX


def get_fighter_photo_url(name: str) -> str | None:
    """Return a URL to the fighter's photo. Local first, then ESPN, then Wikipedia."""
    slug = name.replace(" ", "_").lower()
    local_fname = _photo_index().get(slug)
    if local_fname:
        return f"/fighter_photos/{local_fname}"

    headers = {"User-Agent": "UFC-Fight-Night/11.0"}

    # ESPN
    try:
        r = _requests.get(
            f"https://site.api.espn.com/apis/search/v2?query={_urlparse.quote(name)}&section=mma&limit=5",
            timeout=5,
            headers=headers,
        )
        if r.status_code == 200:
            for group in r.json().get("results", []):
                for item in group.get("contents", []):
                    athlete_id = item.get("id") or item.get("athleteId")
                    if athlete_id:
                        img_url = f"https://a.espncdn.com/i/headshots/mma/players/full/{athlete_id}.png"
                        head = _requests.head(img_url, timeout=4, headers=headers)
                        if head.status_code == 200:
                            return img_url
    except Exception:
        pass

    # Wikipedia
    try:
        wiki_slug = _urlparse.quote(name.replace(" ", "_"))
        r = _requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_slug}",
            timeout=5,
            headers=headers,
        )
        if r.status_code == 200:
            return r.json().get("thumbnail", {}).get("source")
    except Exception:
        pass

    return None


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
