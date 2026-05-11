# Post-Event Reflection System — Design Spec

**Status:** Approved 2026-05-11. Pre-implementation.
**Owner:** Project lead (Zachary)
**Implementation plan:** TBD (to be created by `superpowers:writing-plans` next)

## Goal

Make the fight-prediction system continuously improve over time by reflecting on completed UFC cards and turning calibration errors into per-agent prompt adjustments that take effect on the next refresh cycle. Specifically: when our prediction is wrong (or right for the wrong reasons), we want the relevant specialist agents to know about it and adjust their priors on future predictions.

## Non-goals

- **Not** a metrics dashboard on the user-facing site (phase 2, requires ~1 month of data to be meaningful).
- **Not** automatic prompt rewriting — lessons are appended as additive context to existing agent prompts, never modifying the framework agent files themselves.
- **Not** a model fine-tuning system — we use prompt-engineering, not weight updates.
- **Not** real-time / in-game reflection — purely post-event.

## Locked design decisions (from brainstorming, 2026-05-11)

1. **Success metrics, weighted:** beating the sportsbook closing line (primary), pick accuracy (secondary), probability calibration via Brier score (tertiary). All three are computed deterministically per fight.
2. **Lesson scope:** per-agent filtered. Each lesson is tagged with `applies_to: [agent_names]` and only injects into the relevant specialists' prompts (or the synthesizer's prompt).
3. **Governance:** confidence-gated auto-apply. Lessons live in either an `active` corpus (high confidence, injects into prompts) or a `watchlist` (low/medium confidence, observed only; promotes after ≥3 confirmations).
4. **Visibility:** `lessons.md` is committed to the repo on every reflection run; GHA workflow log prints a delta summary (new findings, promotions, archivals). No notifications.
5. **Model tier:** all Opus 4.7 for the three LLM passes (~$2.80/event, ~$145/yr).
6. **Cadence:** Sunday 12:00 UTC cron + `workflow_dispatch`. Idempotent — skips if no event happened in the past 48h. Retries next Sunday if a scraper fails.

## Architecture

```
[Saturday: UFC event happens]
    ↓
[Sunday 12:00 UTC: .github/workflows/reflect.yml fires]
    ↓
backend/reflection/__main__.py
    ↓
1. detect_completed_events.py
     → list of {event_key, event_url} we predicted on and which are now in the past
    ↓ (for each event)
2. outcome_scraper.py + closing_line_scraper.py
     → outcomes.json + closing_lines.json
    ↓
3. score.py (PURE PYTHON, NO LLM)
     → backend/cache/scores/<event_key>.json
     → append row to backend/cache/metrics_log.jsonl
    ↓
4. reflect_runner.py (Opus 4.7 × 15 calls per event)
     a. Per-fight reflection (13 parallel Opus calls)
     b. Card meta-pass (1 Opus call)
     c. Lesson merge pass (1 Opus call, mutates lessons.json)
    ↓
5. lesson_store.py
     → write backend/cache/lessons.json
     → regenerate backend/cache/lessons.md (human-readable)
     → print delta summary to stdout (for GHA log)
    ↓
6. git add → commit → push (uses the rebase-on-conflict fix from refresh_cache.py)

[Monday 14:00 UTC: refresh-card.yml fires]
    ↓
agent_runner.py and synthesizer.py load lessons.json,
filter by agent + confidence, append to system prompt
```

## Components

### New files

```
backend/reflection/
  __init__.py
  __main__.py                  # CLI entry: `python -m backend.reflection`
  detect_completed_events.py
  outcome_scraper.py
  closing_line_scraper.py      # may reuse existing scrape_bestfightodds.py
  score.py                     # deterministic; pure Python; unit-testable
  reflect_runner.py            # the three LLM passes
  lesson_store.py              # read/write lessons.json + regenerate lessons.md
  prompts/
    per_fight_reflection.md    # the per-fight reflection system prompt
    card_meta_pass.md          # the card-level meta-pass system prompt
    lesson_merge.md            # the lesson-merge system prompt

backend/cache/
  lessons.json                 # source of truth for injection
  lessons.md                   # human-readable mirror, regenerated each run
  metrics_log.jsonl            # append-only, one row per completed event
  scores/<event_key>.json      # per-event deterministic scoring

.github/workflows/reflect.yml  # cron Sun 12 UTC + workflow_dispatch

backend/reflection/tests/
  test_score.py                # unit tests for deterministic scoring
  test_lesson_store.py         # unit tests for read/write/regenerate
```

### Modified files

```
backend/agents/agent_runner.py
  # add _load_lessons_for_agent(agent_name) helper
  # in run_one_agent: append lessons section to system_prompt before client.messages.create

backend/agents/synthesizer.py
  # add _load_synthesizer_lessons() helper
  # append lessons section to instructions before client.messages.create

CLAUDE.md
  # new section: "Reflection pipeline (.github/workflows/reflect.yml)"
  # new bullet in Don't-do-this list: don't manually edit lessons.json — the merge pass owns it
```

## Data schemas

### `backend/cache/scores/<event_key>.json`

Deterministic output of the scoring pass. Never touched by the LLM.

```json
{
  "event_key": "ufc-fight-night-allen-vs-costa__May 16, 2026",
  "event_date": "2026-05-16",
  "reflected_at": "2026-05-17T12:00:00Z",
  "fights": [
    {
      "fight_key": "arnold-allen__melquizael-costa",
      "fighter1": "Arnold Allen",
      "fighter2": "Melquizael Costa",
      "section": "main",
      "predicted": {
        "winner": "Arnold Allen",
        "win_prob": 0.62,
        "our_moneyline_f1": -163,
        "method_probs": { "ko": 0.25, "sub": 0.05, "dec": 0.70 },
        "round_probs": [0.05, 0.10, 0.10, 0.15, 0.60]
      },
      "actual": {
        "winner": "Arnold Allen",
        "method": "Decision",
        "round": 3,
        "time": "5:00",
        "stats": {
          "sig_strikes_f1": 87,
          "sig_strikes_f2": 64,
          "takedowns_f1": 0,
          "takedowns_f2": 0,
          "sub_attempts_f1": 0,
          "knockdowns_f1": 0
        }
      },
      "closing_line": {
        "f1_moneyline": -210,
        "f1_implied_prob": 0.677,
        "source": "bestfightodds",
        "scraped_at": "2026-05-17T12:00:00Z"
      },
      "scoring": {
        "pick_correct": true,
        "method_correct": true,
        "round_correct": true,
        "brier_score": 0.144,
        "log_loss": 0.478,
        "line_beat": {
          "we_said_f1_prob": 0.62,
          "closing_implied_prob": 0.677,
          "bet_signal": "fade",
          "would_have_been_profitable": false,
          "edge_pct": -5.7
        }
      }
    }
  ],
  "card_rollup": {
    "fights_scored": 13,
    "pick_accuracy": 0.769,
    "avg_brier": 0.182,
    "betting_record": {
      "bets_taken": 4,
      "bets_won": 2,
      "roi_pct": -3.2,
      "unit_pl": -12.80
    }
  }
}
```

Notes:
- All `line_beat` math is **fighter1-relative** so the schema is consistent across fights. `we_said_f1_prob` is our model's win prob for fighter1 (derived from `predicted.win_prob` and `predicted.winner`); `closing_implied_prob` is from `closing_line.f1_implied_prob`.
- `bet_signal` is computed from `edge = we_said_f1_prob - closing_implied_prob`:
  - `"back_f1"` if `edge > +0.05` (our model thinks fighter1 is undervalued by the market → bet on f1)
  - `"back_f2"` if `edge < -0.05` (our model thinks fighter2 is undervalued → bet on f2)
  - `"pass"` if `|edge| <= 0.05` (we agree with the market within tolerance — no edge worth betting)
- `would_have_been_profitable` uses standard moneyline math: $100 unit on whichever side `bet_signal` says, settled at the closing line.
- `closing_line` is `null` if scraper failed for that fight; line-beat metrics in `scoring` are then also `null`.

### `backend/cache/metrics_log.jsonl`

Append-only history. One JSON object per line, one line per completed event. Lets us compute rolling trends without parsing every `scores/*.json`.

```jsonl
{"event_key": "ufc-326__Apr 25, 2026", "event_date": "2026-04-25", "fights_scored": 12, "pick_accuracy": 0.667, "avg_brier": 0.213, "bets_taken": 5, "bets_won": 3, "roi_pct": 8.4, "reflected_at": "2026-04-26T12:00:00Z"}
{"event_key": "ufc-fight-night-allen-vs-costa__May 16, 2026", ...}
```

### `backend/cache/lessons.json`

Source of truth for prompt injection. Owned by the merge-pass LLM.

```json
{
  "schema_version": 1,
  "last_updated": "2026-05-17T12:00:00Z",
  "lessons": [
    {
      "id": "lesson_001",
      "applies_to": ["ufc-grappling-offense", "ufc-wrestling-offense"],
      "pattern": "We systematically over-rate grappling-heavy fighters in their UFC debut. Regional tape can't show the cardio/strength gap from the UFC level.",
      "confidence": "high",
      "status": "active",
      "evidence_count": 4,
      "first_seen": "2026-03-15",
      "last_confirmed": "2026-05-16",
      "examples": [
        {
          "event_key": "ufc-326__Apr 25, 2026",
          "fight_key": "smith__jones",
          "what_we_said": "Smith 8/10 grappling-offense",
          "what_happened": "Smith taken down R1, gassed by R2, decision loss"
        }
      ],
      "suggested_correction": "When primary specialist is a UFC debut fighter, cap grappling/wrestling ratings at 7 unless explicit world-class credentials (Olympic medal, ADCC podium, BJJ world champion)."
    }
  ],
  "watchlist": [
    {
      "id": "watch_007",
      "applies_to": ["ufc-striking-defense"],
      "pattern": "Possible under-rating of head-movement specialists against orthodox volume strikers.",
      "confidence": "low",
      "status": "watching",
      "evidence_count": 1,
      "first_seen": "2026-05-16",
      "last_confirmed": "2026-05-16",
      "examples": [...]
    }
  ],
  "archived": [
    {
      "id": "lesson_003",
      "pattern": "...",
      "status": "archived",
      "archived_at": "2026-05-17T12:00:00Z",
      "archived_reason": "Not confirmed in 6 months; possible artifact of small early sample."
    }
  ]
}
```

Promotion rule (enforced by the merge-pass prompt): `watchlist` entry with `evidence_count >= 3` AND `last_confirmed` within the past 8 weeks → promote to `lessons` with `confidence: "high"`.

Archive rule: `lessons` entry with no new `last_confirmed` in 6 months → move to `archived` (not injected, but retained for audit).

### `backend/cache/lessons.md`

Regenerated from `lessons.json` after every reflection. Human-readable view, sorted by `agent → confidence → recency`.

```markdown
# Lessons learned (auto-regenerated 2026-05-17T12:00:00Z)

## ufc-grappling-offense

### [HIGH] lesson_001 — Over-rating debut grapplers
**Pattern:** We systematically over-rate grappling-heavy fighters in their UFC debut. ...
**Correction:** When primary specialist is a UFC debut fighter, cap grappling ratings at 7 ...
**Evidence:** 4 observations since 2026-03-15
**Last confirmed:** 2026-05-16 (Smith vs Jones)
...
```

## Deterministic scoring (`score.py`)

Pure Python, no LLM, fully unit-testable. Inputs:
- `predicted`: dict pulled from `analyses.json` (existing structure — winner pick, win prob, method probs, round probs).
- `actual`: dict from outcome scraper (winner, method, round, time, stats).
- `closing_line`: dict from BestFightOdds scraper (moneyline at fight time, implied prob).

Outputs the `scoring` block in the schema above. Key computations:

```python
# Brier score (lower = better calibration)
brier_score = (predicted_win_prob - actual_outcome_binary) ** 2

# Log loss (penalizes confident-wrong predictions harder)
log_loss = -log(predicted_win_prob if actual_won else 1 - predicted_win_prob)

# Line-beat: would betting our line have been profitable?
# Normalize to f1-relative: our model's prob for fighter1 winning
we_said_f1_prob = (predicted.win_prob if predicted.winner == fighter1
                   else 1 - predicted.win_prob)
edge = we_said_f1_prob - closing_line.f1_implied_prob

if abs(edge) <= 0.05:
    bet_signal = "pass"
elif edge > 0.05:
    bet_signal = "back_f1"   # f1 is undervalued by the market
else:
    bet_signal = "back_f2"   # f2 is undervalued by the market

# Profit at closing line, $100 unit
if bet_signal == "back_f1":
    pl = (100 * (1 - closing_line.f1_implied_prob) / closing_line.f1_implied_prob
          if actual.winner == fighter1 else -100)
elif bet_signal == "back_f2":
    f2_implied = 1 - closing_line.f1_implied_prob
    pl = (100 * (1 - f2_implied) / f2_implied
          if actual.winner == fighter2 else -100)
else:
    pl = 0
```

## LLM reflection passes (`reflect_runner.py`)

All three passes use Opus 4.7. All three have `timeout=300.0` per the project convention.

### Pass 1: per-fight reflection (13 parallel calls)

**System prompt** (`prompts/per_fight_reflection.md`):

> You are a post-fight reviewer for a UFC prediction system. You will be given ONE fight: our 20 specialist agent reports, our synthesizer's prediction, the actual outcome (with fight stats), and a structured scoring of what we got right and wrong. Your job is to identify *specific* patterns in the specialists' reasoning that, if corrected, would have produced a better prediction.
>
> Output a JSON block with this shape: `{ "findings": [ { "responsible_agents": [...], "pattern": "...", "evidence_excerpt": "<quote from specialist report>", "what_actually_happened": "<from outcome stats>", "suggested_correction": "...", "confidence_for_this_fight": "low" | "medium" | "high" } ] }`
>
> Rules:
> - Only emit findings that are concrete and falsifiable. NO generic platitudes like "we should weight cardio more".
> - If we predicted correctly AND for the right reasons, emit `{"findings": []}` — no false-positive lessons.
> - `confidence_for_this_fight` is your read on whether this pattern is likely to repeat; the *cross-fight* confidence is determined later by the merge pass based on evidence_count.

**User payload:** `{ predicted, actual, closing_line, scoring, specialist_reports[20], synthesizer_output }`

### Pass 2: card meta-pass (1 call)

**System prompt** (`prompts/card_meta_pass.md`):

> You will receive the per-fight findings from every fight on a completed UFC card, plus the card-level rollup metrics. Identify which findings show up across multiple fights (cross-fight patterns) versus which are one-off observations.
>
> Output: `{ "card_level_findings": [ { "responsible_agents": [...], "pattern": "...", "fights_supporting": [fight_keys], "confidence_for_this_card": "low|medium|high", "suggested_correction": "..." } ] }`

**User payload:** `{ event_key, card_rollup, per_fight_findings[] }`

### Pass 3: lesson merge (1 call)

**System prompt** (`prompts/lesson_merge.md`):

> You are the curator of a long-running lessons-learned corpus for a UFC prediction system. You will be given (a) the current `lessons.json` and (b) the new card-level findings from this week's reflection. Your job is to produce the updated `lessons.json`.
>
> Rules:
> 1. If a new finding matches an existing `lessons` or `watchlist` entry, increment its `evidence_count` and update `last_confirmed` + `examples`. Do NOT duplicate.
> 2. New findings without a matching entry start in `watchlist` with `confidence: "low"` and `evidence_count: 1`.
> 3. Promote `watchlist` → `lessons` (with `confidence: "high"`) when `evidence_count >= 3` AND `last_confirmed` is within the past 8 weeks.
> 4. Archive any `lessons` entry whose `last_confirmed` is older than 6 months (move to `archived` with `archived_reason`).
> 5. NEVER delete `examples` — only append. The audit trail must persist.
> 6. Output ONLY the updated `lessons.json` as a single fenced JSON block.

**User payload:** `{ current_lessons, new_card_findings, card_meta_findings, event_metadata }`

## Lesson injection contract

Both `agent_runner.run_one_agent` and `synthesizer.synthesize` get a small helper:

```python
def _inject_lessons(system_prompt: str, agent_name: str, max_lessons: int = 5) -> str:
    """Append a 'Field-tested adjustments' section to the system prompt
    if there are relevant high-confidence lessons. Falls back to original
    prompt if lessons.json is missing or empty."""
```

Filter rule:
- Specialists: `lesson["confidence"] == "high"` AND `agent_name in lesson["applies_to"]`. Sort by `last_confirmed` desc. Take top 5.
- Synthesizer: `lesson["confidence"] == "high"` AND `"synthesizer" in lesson["applies_to"]`. Top 8.

Injected section format (appended to existing system prompt):

```
## Field-tested adjustments from past predictions

The following patterns have been observed in past predictions. Use them as PRIORS that adjust your default reasoning, NOT as overriding rules. If the current dossier directly contradicts a prior, trust the dossier.

- PATTERN: <pattern>
  CORRECTION: <suggested_correction>
  EVIDENCE: <n> observations since <first_seen>

[... up to 5 (specialists) or 8 (synthesizer) lessons ...]
```

Token budget: ~150 tokens/lesson × 5 = ~750 extra tokens per specialist system prompt. Acceptable (specialist prompts are currently ~3K tokens).

## Error handling

| Failure | Behavior |
|---|---|
| `detect_completed_events` finds no event in past 48h | Log "no event to reflect on", exit 0. |
| `outcome_scraper` fails (ufcstats slow, parse error) | Log, skip this event, retry next Sunday. Idempotent. |
| `closing_line_scraper` fails | Continue with `closing_line: null`; `line_beat` metrics also null. Other metrics still compute. |
| LLM call 500s / JSON parse error | Retry 3× with exponential backoff. If still failing, fall back to `{"findings": []}` for that fight. |
| No prediction in `analyses.json` for an event we should have | Log warning, skip (we can't reflect on something we didn't predict). |
| `lessons.json` parse error | Read previous version from `git show HEAD:backend/cache/lessons.json`. If that also fails, start from empty `{}` (log loudly). |
| Git push race | Already handled by `_commit_and_push` rebase-on-conflict in refresh_cache.py. Mirror the same logic in reflection commits. |

## Testing strategy

### Unit tests (must pass before merge)

- `test_score.py` — feeds known prediction + outcome dicts → asserts each scoring field. ~12 cases covering all winner/method/round/line-beat combos.
- `test_lesson_store.py` — round-trip read/write of `lessons.json`; assert `lessons.md` regeneration matches a golden file.

### Smoke tests (run once, then ad-hoc)

- Run `outcome_scraper.py` against a known past event (e.g., UFC 327, completed weeks ago); assert known outcomes match.
- Run `closing_line_scraper.py` against the same event; assert known closing lines match within tolerance.

### Integration (manual, post-deploy)

- After first deploy, run `python -m backend.reflection --dry-run` against the most recent completed event. Inspect the would-be `lessons.json` diff. If reasonable, run without `--dry-run`.

### Lesson-injection regression

- Place a known lesson in `lessons.json`, run `agent_runner.run_one_agent` on a fixed dossier with mocked Anthropic client; assert the lesson text appears in the user payload sent to the client.

## Cost

| Pass | Model | Calls/event | Tokens | Cost/event |
|---|---|---|---|---|
| Per-fight reflection | Opus 4.7 | 13 (parallel) | ~3K in / 1K out each | ~$1.56 |
| Card meta-pass | Opus 4.7 | 1 | ~30K in / 2K out | ~$0.60 |
| Lesson merge | Opus 4.7 | 1 | ~25K in / 4K out | ~$0.68 |
| **Total** | | | | **~$2.85/event** |

At ~1 event/week: ~$11.40/month, ~$145/year. Refresh pipeline is unaffected (~$35-60/week as before).

## Schedule

Cron in `.github/workflows/reflect.yml`:

```yaml
on:
  schedule:
    - cron: "0 12 * * 0"   # Every Sunday 12:00 UTC
  workflow_dispatch: {}
```

Idempotent: if no event in past 48h, exits in <30s. UFCStats stats are usually published within 12h of fight finish, so Sunday 12 UTC (~7 AM CDT) catches Saturday fights cleanly. If stats aren't there yet, next Sunday retries.

## Out of scope (phase 2 ideas — do not build now)

- `/metrics` page on the deployed site showing rolling Brier score and ROI vs. closing line
- Per-specialist scorecards (requires 50+ fights of data to be statistically meaningful)
- Alerts/notifications when a watchlist lesson gets promoted to active
- Closing-line shopping across multiple sportsbooks (currently single source: BestFightOdds)
- Reflection on prelim fights only / main-card-only filters

## Open questions (none blocking)

None — all design decisions locked in brainstorming on 2026-05-11.

## Acceptance criteria

The reflection system is considered shipped when:

1. `.github/workflows/reflect.yml` runs successfully on a manual `workflow_dispatch` against the most recent completed UFC event, end-to-end (detect → scrape → score → reflect → commit).
2. `backend/cache/lessons.json` and `lessons.md` are committed to the repo with at least one populated `watchlist` entry.
3. `backend/cache/scores/<event_key>.json` exists for the test event with all 13 fights scored.
4. A subsequent `refresh-card.yml` run successfully loads `lessons.json` and injects (at minimum) zero high-confidence lessons (because we have no high-confidence lessons yet — the test is that the *mechanism* works, not that the data is full).
5. All unit tests pass.
6. CLAUDE.md updated with a "Reflection pipeline" section and a "don't manually edit lessons.json" entry in the don't-do-this list.
