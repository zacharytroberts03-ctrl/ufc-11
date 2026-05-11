# UFC 11 Fight Analyzer — Project Context

This file is the orientation guide for any Claude session (or human) working on this repo. Read it first; it covers architecture, conventions, and the decisions that are NOT obvious from reading code.

## TL;DR

**Brand: FightZ** (was UFCZ — renamed 2026-05-05 to avoid Zuffa/UFC trademark risk). Scrapes the upcoming UFC card, runs 10 specialist Claude agents per fighter, synthesizes a fight prediction + betting recommendations, publishes the results as static JSON, and deploys to Vercel via CLI. Live at **https://www.ufc-z.com/** (custom domain on Cloudflare DNS, served by the `frontend` Vercel project).

- **App name:** FightZ
- **Primary domain (current):** `https://www.ufc-z.com/` (apex `ufc-z.com` 307-redirects to `www`)
- **Legacy URL still live:** `https://frontend-rouge-mu-86.vercel.app/`
- **GitHub repo:** `https://github.com/zacharytroberts03-ctrl/ufc-11`
- **Vercel team:** `zacharytroberts03-ctrls-projects`, project `frontend` (the `backend` Vercel project is a legacy FastAPI deploy, not used by current static-JSON pipeline)

## ⚠️ PENDING: Domain swap before App Store submission

The app name is FightZ but the domain still contains "ufc-z" — that's a deliberate transitional state. Before App Store submission, swap to a clean domain (e.g., `fightz.app` or `fightz.io`) so the brand and URL match and there's zero residual UFC-trademark exposure.

**When to trigger:** when the user is about to submit the app to the App Store, or anytime the user explicitly mentions "publishing", "going live", "App Store submission", or similar. Remind them proactively at that point.

**What to do at swap time:**
1. User registers the new domain in Cloudflare (~5 min, ~$10–15)
2. User adds it to Vercel `frontend` project + sets it as primary domain
3. I find-and-replace `ufc-z.com` → new domain across: `CLAUDE.md`, `frontend/app/privacy/page.tsx`, `frontend/app/terms/page.tsx`, any other strings
4. User sets up 301 redirect from `ufc-z.com` → new domain in Cloudflare Page Rules
5. User re-points Newly app config to new domain
6. User updates App Store Connect listing if already submitted

## Architecture in one paragraph

Backend Python scripts (running on the user's local Windows machine, not on Vercel) scrape ufcstats.com + Tapology for the upcoming UFC event, run a Claude-based agent pipeline to produce per-fight analyses, write the results as JSON to `frontend/public/data/{card.json,analyses.json}`, commit + push to GitHub, then run `npx vercel --prod` to deploy. The Next.js frontend reads those static JSON files at request time. There is no live Python backend serving traffic.

## Directory map

```
ufc-11/
├── CLAUDE.md                       ← you are here
├── UFC agents/                     ← framework: 10 specialist agent files (5 offense + 5 defense)
│   ├── README.md                   ← framework documentation, read this for agent behavior
│   ├── _shared/{output-schema, data-contract, archetype-taxonomy}.md
│   ├── offense/ufc-{striking,wrestling,takedown,grappling,submission}-offense.agent.md
│   └── defense/ufc-{...}-defense.agent.md
├── backend/
│   ├── analysis_runner.py          ← orchestrator: scrape → agents → synthesizer → return dict
│   ├── main.py                     ← legacy FastAPI; only `get_fighter_photo_url` is still relevant
│   ├── cache.py                    ← per-fight result cache (analyses.json)
│   ├── agents/
│   │   ├── dossier.py              ← scrape output → data-contract.md shape
│   │   ├── agent_runner.py         ← loads agent files, fans out 20 parallel Claude calls per fight
│   │   ├── agent_cache.py          ← per-(fighter,agent,opponent,last_fight_date) cache
│   │   ├── synthesizer.py          ← deterministic domain-advantage table + LLM aggregator → bets JSON + analysis_sections markdown
│   │   └── fighter_overrides.py    ← MANUAL data fills for fields scrapers can't get (e.g., camp)
│   ├── tools/
│   │   ├── scrape_ufc_card.py      ← upcoming-card scraper with TEMPORAL event-priority logic
│   │   ├── scrape_ufc_fighter.py   ← fighter dossier scraper (handles hyphenated names, nicknames)
│   │   ├── scrape_tapology.py      ← intangibles: camp, nationality, fights_out_of, weight-miss
│   │   ├── scrape_debut_fighter.py ← Tapology fallback for non-UFC fighters
│   │   ├── scrape_odds.py          ← The Odds API
│   │   ├── scrape_bestfightodds.py ← line-movement scraper
│   │   ├── altitude_lookup.py      ← venue altitude
│   │   └── hedge_calculator.py     ← arbitrage / hedge math
│   ├── rules/BETTING_AI_RULES.md   ← curated betting heuristics injected into synthesizer system prompt
│   ├── scripts/
│   │   ├── refresh_cache.py        ← THE main daily entry point (called by scheduled task)
│   │   └── refresh_intangibles.py  ← cheap Tapology-only refresh (no Claude API spend)
│   └── cache/
│       ├── analyses.json           ← per-fight final results (also in frontend/public/data/)
│       ├── agent_reports.json      ← specialist reports keyed by (fighter,agent,opponent,date)
│       └── refresh.log             ← scheduled task log
├── frontend/                       ← Next.js 16 app
│   ├── app/
│   │   ├── page.tsx                ← homepage: card listing
│   │   ├── layout.tsx              ← header + footer (NO "AI" labels per user)
│   │   └── fight/[f1]/[f2]/page.tsx ← fight detail page
│   ├── components/
│   │   ├── FighterVsHeader.tsx     ← photos + names + decagons + 3-line bio (From/Out of/Team)
│   │   ├── FighterDecagon.tsx      ← SVG 10-axis radar chart
│   │   ├── DecagonKey.tsx          ← OFFENSE/DEFENSE legend panels (flank the VS header)
│   │   ├── FavoriteFighterPanel.tsx ← "The Favorite Fighter" tab content (pick + calculated odds + disclaimer)
│   │   ├── AnalysisSection.tsx     ← collapsible content card; accepts `content` (markdown) OR `children` (JSX)
│   │   ├── FightTile.tsx           ← homepage card row
│   │   └── EventBanner.tsx         ← homepage event header
│   ├── lib/
│   │   ├── api.ts                  ← fetches /data/card.json + /data/analyses.json
│   │   ├── types.ts                ← AnalysisResult, BetsObject, DomainAdvantages, FighterIntangibles
│   │   ├── photoUrl.ts             ← derives /fighter_photos/<First>_<Last>.jpg from name
│   │   ├── flagEmoji.ts            ← country name → ISO code → Twemoji SVG URL
│   │   └── odds.ts                 ← win prob ↔ American moneyline conversion
│   └── public/
│       ├── data/{card.json, analyses.json}  ← the data the frontend reads
│       └── fighter_photos/<First>_<Last>.jpg  ← static photo assets
├── setup_schedule.ps1              ← registers Windows scheduled task `CardDealsUpdater`
└── run_card_deals.bat              ← bat file the scheduled task invokes
```

## The agent pipeline (read before touching `backend/agents/`)

Per fight, the pipeline does this:

1. `_scrape_one(name)` → returns a fighter dossier (UFCStats primary, Tapology fallback for debut fighters).
2. `build_dossier()` adapts that to the shape `UFC agents/_shared/data-contract.md` requires.
3. `run_all_agents_for_fight()` fans out **20 parallel Claude calls** (10 agents × 2 fighters as primary). Each agent emits `{JSON, narrative}`. Caching is by `(fighter, agent, opponent, last_fight_date)` — opponent-agnostic fields naturally re-cache when opponents change.
4. `synthesize()` runs a final aggregator call: it computes a deterministic 5-domain advantage table from the 20 ratings, then asks Claude to produce the 5 markdown sections the frontend already renders **plus** a structured `bets` JSON block (moneyline, method probabilities, distance, rounds, key thesis, supporting specialists).
5. `analysis_runner.run_analysis()` returns one big dict combining all of the above + side data (odds, hedge, line movement, intangibles).

**Model selection** (Option C: hybrid):
- Main card (top 5 fights, `section: "main"`): **Opus 4.7**
- Prelims (rest, `section: "prelim"`): **Sonnet 4.6**

**Critical: do NOT pass `temperature` to Opus 4.7 calls.** Opus 4.7 deprecated user-set temperature and returns 400. Both `agent_runner.py` and `synthesizer.py` already gate temperature on `not model.startswith("claude-opus-4-7")`.

**Schema reinforcement:** in `agent_runner._build_user_payload`, every user message gets a literal schema reminder appended. Sonnet (and even Opus occasionally) drifts and invents field names like `output_trend` instead of `recent_trend` if you don't pin the schema explicitly at the call site.

## Deployment

**Vercel project is NOT linked to GitHub auto-deploy.** Every previous deploy in `vercel ls` was a manual CLI invocation. Don't assume a `git push` triggers a deploy — it does not. Discovery date: 2026-05-01, when the site sat 6 days stale despite daily git pushes. The fix lives in `refresh_cache.py::_vercel_deploy()` which runs `npx vercel --prod --yes --cwd frontend` after the git push.

If anyone (you, future me, the user) wires up the GitHub integration in the Vercel dashboard later, **delete `_vercel_deploy()` from refresh_cache.py** to avoid double-deploys, and update this file.

## Schedule (Windows scheduled task `CardDealsUpdater`)

- **Triggers:** Mon 9:00 AM, Wed 2:00 PM, Fri 8:00 PM (weekly)
- **Settings:** `StartWhenAvailable=True`, `WakeToRun=True`, runs on battery, 2h execution-time limit
- **Caveat:** `WakeToRun` only works from sleep, not from full shutdown. Full shutdown still misses the trigger; `StartWhenAvailable` catches up on next boot.
- **Stale-event guard:** `refresh_cache.py` aborts (exit code 5) if the scraped event date is more than 7 days old. This catches edge cases where the priority logic falls into the last-resort branch and prevents silently deploying week-old fights.

To re-register / change the schedule, edit `setup_schedule.ps1` and run it again as Administrator.

## Event-priority logic (in `scrape_ufc_card.py::find_current_event`)

Forward-looking priority — DO NOT FLIP THIS without understanding the failure modes:

1. Event happening today (catches fight day even if ufcstats moves the event to "completed" before midnight)
2. Next upcoming event (the common case — site previews next week's card)
3. Most recent past event as last resort (only when ufcstats hasn't listed any upcoming event yet)

History of this logic:
- Original future-first → premature jump-ahead on fight Saturdays (UTC/local timezone skew) — fixed by adding "today" as priority 1.
- Past-first (`6e2896e`) → 6-day-stale site Tue-Fri before next fight night — fixed by reverting.
- 2-day post-fight reflection window added 2026-05-01 → caused Monday refreshes to keep showing the previous Saturday's already-over fight instead of next week's preview. Removed 2026-05-11 per user direction.

Don't re-add a past-event window without an explicit user request — the user prefers forward-looking content. The "today" priority handles the fight-Saturday case without needing a reflection window.

## App Store launch project (active workstream)

A separate doc tracks the App Store submission plan: `docs/app-store-listing.md` has the App Name, subtitle, keywords, full description draft, App Privacy answers, and submission checklist. Pull that up at submission time.

Current state (2026-05-07): Phase 1 web prep done, Clerk auth + paywall + account pages live, RevenueCat account created. Apple Developer Program enrolled but not yet approved. Wrapper service (Newly/Median/Capacitor) deliberately deferred until close to deploy — when that conversation opens, **verify any service URL independently before recommending it**. Detailed status lives in the private memory at `~/.claude/.../project_ufc_11.md`.

## Frontend conventions

- **Theme is dark** despite some Tailwind color names suggesting otherwise. The `ufc-surface` token is `#ffffff` (legacy, light-themed) but actual cards use `bg-[#0d0d0d]` / dark gradients. Don't add new white surfaces.
- **No "AI" branding** — the user removed every "AI" mention from header, footer, fight headings, and metadata. Keep it that way unless the user reverses that.
- **Photos are relative paths** (`/fighter_photos/<First>_<Last>.jpg`) — never hardcode the Vercel domain. Helpers in `lib/photoUrl.ts` derive from name as fallback when JSON data is missing the URL.
- **Country flags use Twemoji SVGs** via CDN (`cdn.jsdelivr.net/gh/twitter/twemoji@latest/...`) because Windows Segoe UI Emoji renders flag regional-indicator pairs as letters ("RU AE US"). Helper in `lib/flagEmoji.ts`.
- **Fight detail page sections start collapsed** (Style & Profile, Head-to-Head, Endings, The Favorite Fighter). Don't change `defaultOpen` to `true` without checking with the user.
- **The Favorite Fighter tab** (NOT "Betting Recommendation") shows: pick + win %, calculated American moneyline odds, confidence, key thesis, and a disclaimer that we do NOT pull odds from any sportsbook — these are computed from our analysis alone.
- **Decagon labels:** unique acronyms `O-STR / D-STR / O-WRS / D-WRS / ...`. Both keys flank the VS header (offense red on left, defense gold on right) and stretch full height to match.
- **FighterVsHeader layout:** 3-column grid `[F1 stack | VS | F2 stack]` on every screen size. Each fighter is a vertical stack: photo → name → decagon → details (From/Fighting Out of/Team). The decagons sit at the same row position so they're directly side-by-side. Don't put photos on the outer flanks of the card — that was the old layout pre-2026-05-07.
- **FightTile (homepage list):** photo+name stack vertically on phone (`flex-col`), side-by-side on `sm:` and up. Names use `break-words`, NOT `truncate`, so full names are always visible — App Store screenshots looked terrible with the truncated "K..." / "Jos..." version.
- **Auth in header:** plain `<a>` links to `/sign-in` and `/sign-up` (NOT Clerk's `mode="modal"` buttons). Modal mode had unfixable dark-theme issues; the dedicated pages render cleanly via @clerk/themes' `dark` baseTheme on ClerkProvider.

## Manual data overrides

Tapology's `Affiliation` field is empty for some fighters (no scraper can fix that). Use `backend/agents/fighter_overrides.py` to fill gaps:

```python
OVERRIDES = {
    "Waldo Cortes Acosta": {"camp": "UKF Gym"},
    # add more as discovered
}
```

Manual values fill missing fields only; scraped values always win. Wired into both `analysis_runner.py` and `refresh_intangibles.py`.

## Cost model (real numbers from production)

- **Per main-card fight (Opus 4.7):** ~$5–$8 (20 specialist + 1 synthesizer call)
- **Per prelim (Sonnet 4.6):** ~$1–$2
- **Full uncached UFC card (5 main + 8 prelim):** ~$30–$50
- **Same card, second/third refresh (specialists cache hit, synthesizer re-runs to incorporate fresh odds):** ~$2–$5
- **Weekly cost (3 refreshes/week, one new card most weeks):** ~$35–$60

Cost levers if needed: drop main card to Sonnet (~70% reduction), skip the Wed refresh, or skip refreshes when scraped `event_key` matches the last analyzed one.

## Common operations

| Task | Command |
|---|---|
| Manual refresh of full card | `cd backend && python scripts/refresh_cache.py` (~30 min, ~$30-50) |
| Refresh just intangibles (free, fast) | `cd backend && python scripts/refresh_intangibles.py` |
| Smoke test one fight | edit `analysis_runner.run_analysis(...)` call, ~$0.40-$8 depending on model |
| Deploy frontend manually | `cd frontend && npx vercel --prod --yes` |
| Re-register scheduled task | run `setup_schedule.ps1` as Administrator |
| Add a fighter override | edit `backend/agents/fighter_overrides.py`, then run `refresh_intangibles.py` |
| Inspect cache | `backend/cache/analyses.json` and `backend/cache/agent_reports.json` |
| Inspect last refresh | `backend/cache/refresh.log` |

## Strategic direction

**Subscription product (recorded 2026-05-05):** the user is evaluating turning this into a paid subscription. Not started — wait for explicit go-ahead. When that conversation opens, the relevant cost-vs-revenue math is in the "Cost model" section above; the cache strategy gets way more valuable when multiple users share the same precomputed analyses.

## Don't-do-this list (consolidated from past bugs)

- Don't pass `temperature` to Opus 4.7+ models (deprecated, returns 400).
- Don't assume `git push` triggers a Vercel deploy (it doesn't — see Deployment section).
- Don't use Cloudflare's orange-cloud proxy on the Vercel DNS records (breaks SSL).
- Don't hardcode `https://frontend-rouge-mu-86.vercel.app` or any Vercel domain in code or data files. Use relative paths.
- Don't rename the Tapology output keys (`camp`, `nationality`, `fights_out_of`) — the dossier adapter and frontend types depend on them.
- Don't flip the event-priority order in `find_current_event` without re-reading the section above.
- Don't add the "AI" word back to UI strings (user explicitly removed it).
- Don't store API keys outside `c:/Users/Owner/Desktop/Claude/.env` (workspace-level — backend reads with `dotenv` from there).

## Update protocol — keep this file alive

**When to update this file** (do it BEFORE ending the session):

| Change type | Update needed |
|---|---|
| New file added under `backend/` or `frontend/components/` | Add to "Directory map" |
| Schedule, deploy mechanism, or domain changes | Update "Deployment" / "Schedule" / TL;DR |
| New "don't do this" lesson learned | Add to "Don't-do-this list" |
| Strategic direction shift (subscription, monetization, scope) | Update "Strategic direction" |
| New common operation worth documenting | Add row to "Common operations" |
| New fighter override added | No update — `fighter_overrides.py` is self-documenting |
| Pure bug fix or refactor that doesn't change architecture | No update needed |

**How to update:** just `Edit` the relevant section. Keep entries terse. If a section grows past ~15 lines, look for things to compress or split out.

If you (the assistant) made a non-trivial architectural change and forgot to update this file, the session was incomplete. Treat updating this file as part of the work, not as a separate task.

For machine-state notes that DON'T belong in the repo (workspace path, user preferences, machine-specific quirks), use the private memory at `C:\Users\Owner\.claude\projects\c--Users-Owner-Desktop-Claude\memory\project_ufc_11.md` — that file is the same idea but local-only.
