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
