"""Refresh the cached analyses for the upcoming UFC card and publish to the
deployed Vercel site by committing the JSON to the repo.

Pipeline:
  1. Scrape the upcoming card (ufcstats).
  2. Run run_analysis() on every fight, writing results to backend/cache/analyses.json.
  3. Build a card.json mirroring the /api/card endpoint shape.
  4. Copy both JSON files into frontend/public/data/ (read by the deployed frontend).
  5. git add / commit / push so Vercel auto-deploys the fresh data.

Invoked daily by the CardDealsUpdater scheduled task (run_card_deals.bat).
"""

import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))  # ufc-11/
WORKSPACE_ROOT = os.path.abspath(os.path.join(PROJECT_DIR, os.pardir))  # Claude/
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
FRONTEND_DATA_DIR = os.path.join(FRONTEND_DIR, "public", "data")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "tools"))

from dotenv import load_dotenv

# main.py loads backend/.env; we mirror that and also fall back to the workspace .env
load_dotenv(os.path.join(BACKEND_DIR, ".env"))
load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"))

if not os.environ.get("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set in environment or .env", file=sys.stderr)
    sys.exit(2)

from scrape_ufc_card import scrape_upcoming_card
from analysis_runner import run_analysis
from cache import fight_key, load_cache, save_cache, CACHE_FILE
from main import get_fighter_photo_url  # photo URL helper, identical to /api/card


def _slug(s: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")


def _split_card(card: dict) -> dict:
    """Mirror the /api/card endpoint: split fights into main_card / prelims and
    populate per-fighter image URLs."""
    out = {
        "event_name": card["event_name"],
        "date": card["date"],
        "location": card["location"],
        "event_url": card["event_url"],
        "main_card": [],
        "prelims": [],
    }
    for fight in card.get("fights", []):
        enriched = dict(fight)
        enriched["f1_img"] = get_fighter_photo_url(fight["fighter1"])
        enriched["f2_img"] = get_fighter_photo_url(fight["fighter2"])
        bucket = "main_card" if fight.get("section") == "main" else "prelims"
        out[bucket].append(enriched)
    return out


def _publish_to_frontend(cache: dict, card_payload: dict) -> None:
    os.makedirs(FRONTEND_DATA_DIR, exist_ok=True)
    with open(os.path.join(FRONTEND_DATA_DIR, "analyses.json"), "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, default=str)
    with open(os.path.join(FRONTEND_DATA_DIR, "card.json"), "w", encoding="utf-8") as f:
        json.dump(card_payload, f, indent=2, default=str)
    print(f"Published to {FRONTEND_DATA_DIR}")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


def _commit_and_push() -> None:
    """Stage the published JSON, commit, push. Best-effort — log failures but
    don't crash the daily refresh."""
    rel_paths = [
        "frontend/public/data/card.json",
        "frontend/public/data/analyses.json",
        "backend/cache/analyses.json",
    ]
    add = _git("add", "--", *rel_paths)
    if add.returncode != 0:
        print(f"git add failed: {add.stderr}", file=sys.stderr)
        return

    diff = _git("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("No data changes to commit")
        return

    today = datetime.date.today().isoformat()
    commit = _git("commit", "-m", f"chore: daily card refresh ({today})")
    if commit.returncode != 0:
        print(f"git commit failed: {commit.stderr}", file=sys.stderr)
        return
    print(commit.stdout.strip())

    push = _git("push")
    if push.returncode != 0:
        print(f"git push failed: {push.stderr}", file=sys.stderr)
        return
    print("Pushed to origin")


def _vercel_deploy() -> None:
    """Push the frontend to Vercel production. The frontend Vercel project is
    not wired to GitHub auto-deploy, so we deploy from the CLI here. Best-effort:
    log failures but don't crash the refresh.

    Why: missing this step left the deployed site 6 days stale on 2026-05-01 even
    though git pushes were succeeding."""
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        print("vercel deploy skipped: npx not on PATH", file=sys.stderr)
        return
    proc = subprocess.run(
        [npx, "--yes", "vercel", "--prod", "--yes", "--cwd", FRONTEND_DIR],
        cwd=FRONTEND_DIR,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if proc.returncode != 0:
        print(f"vercel deploy failed (exit {proc.returncode}): {proc.stderr.strip()}", file=sys.stderr)
        return
    print("Deployed to Vercel production")


def main() -> int:
    started = time.monotonic()
    print(f"[{datetime.datetime.now().isoformat()}] refresh_cache starting")

    card = scrape_upcoming_card()
    fights = card.get("fights", [])
    if not fights:
        print("No fights parsed — aborting before clobbering cache", file=sys.stderr)
        return 3

    # Stale-event guard: scraper has historically picked a past event when
    # ufcstats listings shift. With temporal logic the worst legitimate case is
    # a fight 2 days ago (post-fight reflection window). Anything older means
    # the priority logic fell into the last-resort branch — refuse to publish.
    try:
        event_date = datetime.datetime.strptime(card["date"], "%B %d, %Y").date()
    except ValueError:
        print(f"Could not parse event date {card['date']!r} — aborting", file=sys.stderr)
        return 4
    days_old = (datetime.date.today() - event_date).days
    if days_old > 7:
        print(
            f"Selected event {card['event_name']} is {days_old} days old "
            f"({card['date']}) — refusing to publish stale data",
            file=sys.stderr,
        )
        return 5

    event_key = f"{_slug(card['event_name'])}__{card['date']}"
    print(f"Event: {card['event_name']} ({card['date']}) — {len(fights)} fights")

    cache = load_cache()

    if cache.get("event_key") != event_key:
        print(f"New event detected (was {cache.get('event_key')!r}) — resetting cache")
        cache = {"event_key": event_key, "generated_at": None, "fights": {}}
    else:
        cache["event_key"] = event_key

    successes = 0
    failures = 0
    for i, fight in enumerate(fights):
        f1 = fight["fighter1"]
        f2 = fight["fighter2"]
        key = fight_key(f1, f2)
        section = fight.get("section", "prelim")
        is_main_event = (i == 0)

        print(f"  [{i + 1}/{len(fights)}] {f1} vs {f2} ({section})")
        try:
            result = run_analysis(
                f1_name=f1,
                f2_name=f2,
                event_context={
                    "location": card.get("location", "Unknown"),
                    "scheduled_rounds": 5 if is_main_event else 3,
                    "is_main_event": is_main_event,
                    "is_title_fight": False,
                    "section": section,  # "main" or "prelim" — drives Opus/Sonnet model pick
                },
            )
            cache["fights"][key] = result
            successes += 1
            cache["generated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            save_cache(cache)
        except Exception as e:
            failures += 1
            print(f"    FAILED: {e!r}", file=sys.stderr)
            traceback.print_exc()

    if successes == 0:
        print("All fights failed — not publishing", file=sys.stderr)
        return 1

    card_payload = _split_card(card)
    _publish_to_frontend(cache, card_payload)
    _commit_and_push()
    _vercel_deploy()

    elapsed = time.monotonic() - started
    print(
        f"[{datetime.datetime.now().isoformat()}] refresh_cache done — "
        f"{successes} ok, {failures} failed, {elapsed:.0f}s"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
