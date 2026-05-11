# UFC Agents — Handoff Context

**For the bot working on the UFC site.** Read this file first; it's the only context you need to start using these agents.

---

## What this folder is

10 specialist UFC analyst agents — 5 offense + 5 defense — that each produce a structured scouting report on one fighter in one specific area of the fight. Hand them a fighter dossier (and optionally a named opponent), get back a JSON-structured report you can ingest into the site.

Together, the 10 agents replace the single generalist Claude pass currently in `ufc-11/backend/analysis_runner.py` with deeper, parallelizable, per-domain analysis.

```
UFC agents/
├── README.md                          ← you are here
├── _shared/
│   ├── output-schema.md               ← JSON shape every agent emits
│   ├── data-contract.md               ← required fighter dossier fields
│   └── archetype-taxonomy.md          ← shared lexicon for "fighter types"
├── offense/
│   ├── ufc-striking-offense.agent.md
│   ├── ufc-wrestling-offense.agent.md
│   ├── ufc-takedown-offense.agent.md
│   ├── ufc-grappling-offense.agent.md
│   └── ufc-submission-offense.agent.md
└── defense/
    ├── ufc-striking-defense.agent.md
    ├── ufc-wrestling-defense.agent.md
    ├── ufc-takedown-defense.agent.md
    ├── ufc-grappling-defense.agent.md
    └── ufc-submission-defense.agent.md
```

---

## The 5 categories — and why they don't overlap

| Category | Offense agent covers | Defense agent covers |
|---|---|---|
| **Striking** | Output, power, accuracy, combinations, footwork-to-attack | Head movement, blocks, distance, durability, footwork-to-evade |
| **Wrestling** | Wrestling base/style, clinch, top-control quality (the *system*) | Staying-on-feet, clinch defense, getup ability, anti-grappling pressure |
| **Takedowns** | The *discrete act* — shot entries, trips, completion %, setups | The *discrete act* — sprawl, hip control, separation, TDD% |
| **Grappling** | Post-takedown top game — scrambles, advancement, pressure, GnP, control time | Bottom game — escapes, scrambles out, surviving control, recovering position |
| **Submissions** | Sub attacks — threat rate, finishes, choke vs joint-lock specialty | Sub defense — choke defense, joint-lock defense, awareness, escape ability |

The boundaries are tight on purpose. If two agents are saying the same thing, sharpen their prompts.

---

## How to invoke an agent

Each agent is a markdown file with YAML frontmatter and a system-prompt body. Pseudocode:

```python
import yaml, anthropic, re

def load_agent(path):
    raw = open(path, encoding="utf-8").read()
    parts = re.split(r"^---\s*$", raw, maxsplit=2, flags=re.M)
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return frontmatter, body

def run_agent(agent_path, primary_fighter, opponent, dossier, opponent_dossier=None):
    fm, system_prompt = load_agent(agent_path)
    client = anthropic.Anthropic()
    user_payload = {
        "primary_fighter": primary_fighter,
        "opponent": opponent,
        "dossier": dossier,
        "opponent_dossier": opponent_dossier,
    }
    resp = client.messages.create(
        model="claude-opus-4-7",          # or fm["model"] mapped to a real ID
        max_tokens=4096,
        temperature=0.4,
        system=system_prompt,
        messages=[{"role": "user", "content": json.dumps(user_payload)}],
    )
    return parse_report(resp.content[0].text)  # extract JSON block + narrative
```

Note: `fm["model"]` in the agent files says `opus`. Map this to a real model ID at call time (`claude-opus-4-7` recommended for analysis depth; `claude-sonnet-4-6` if cost matters).

---

## The fight pipeline

For an upcoming fight `A vs B`:

1. **Fetch dossiers** for both fighters. Use `ufc-11/backend/tools/scrape_ufc_fighter.py` (UFC-roster fighters), with `scrape_tapology.py` and `scrape_debut_fighter.py` as fallbacks for non-UFC fighters. The scraped output should match `_shared/data-contract.md`.

2. **Run all 20 calls in parallel** — 10 agents × 2 fighters as primary:
   ```python
   tasks = []
   for agent_path in glob.glob("UFC agents/{offense,defense}/*.agent.md"):
       tasks.append(run_agent(agent_path, A.name, B.name, A.dossier, B.dossier))
       tasks.append(run_agent(agent_path, B.name, A.name, B.dossier, A.dossier))
   reports = await asyncio.gather(*tasks)
   ```
   On Opus, each call returns in ~3–6s. Parallel = total wall time ~6s.

3. **Collect & cache** — index reports by `(fighter_name, agent_name)`. Cache by `(fighter_name, agent_name, dossier.last_fight_date)` so reports survive across multiple fight cards until that fighter has a new fight.

4. **Aggregate** — optionally run a final synthesis pass: feed the 20 reports + dossiers to a generalist Claude call that produces the fight prediction, key-to-victory, and round-by-round read. The 20 reports are the *substrate*; the aggregator is the *story*.

---

## Input contract → see `_shared/data-contract.md`

Every agent expects a fighter dossier with at minimum: `name`, `record`, `dob`, `height_in`, `reach_in`, `stance`, `striking_stats`, `grappling_stats`, `last_5_fights`, `notable_wins`, `notable_losses`, `last_fight_date`. Most of these are produced directly by `ufc-11/backend/tools/scrape_ufc_fighter.py`.

When a field is missing, agents lower their `confidence` and explain in `data_caveats`. Agents will never fabricate.

## Output contract → see `_shared/output-schema.md`

Every agent emits one fenced ```json``` block with the same shape (only `agent` name and `sub_ratings` keys differ between agents), followed by a 200–400 word markdown narrative.

```json
{
  "agent": "...",
  "fighter": "...",
  "opponent": "...",
  "rating_1_to_10": <int>,
  "sub_ratings": { ... },
  "strengths": [...],
  "weaknesses": [...],
  "signature_techniques": [...],
  "effective_vs_archetypes": [{ "archetype": "...", "why": "..." }],
  "vulnerable_to_archetypes": [{ "archetype": "...", "why": "..." }],
  "matchup_notes_vs_opponent": { ... } | null,
  "recent_trend": "improving|declining|stable",
  "trend_evidence": "...",
  "cardio_factor": "...",
  "durability_factor": "...",
  "camp_and_coaching_notes": "...",
  "key_stats_cited": [{"stat": "...", "value": ..., "source": "..."}],
  "confidence": "high|medium|low",
  "data_caveats": [...]
}
```

## Archetype taxonomy → see `_shared/archetype-taxonomy.md`

Shared lexicon so all agents describe "fighter types" the same way. Agents pick from this list when filling `effective_vs_archetypes` and `vulnerable_to_archetypes`. Lets the site stitch reports together — "this fighter is vulnerable to pressure boxers" means the same thing in every report.

---

## Recommended model & temperature

- **Model:** `claude-opus-4-7` (Opus 4.7 — analysis depth matters here)
- **Temperature:** `0.4` (factual, but not robotic — reports should read like a corner coach, not a stat sheet)
- **max_tokens:** `4096` per call (reports run ~1.5–3K tokens out)

For cost-sensitive runs you can drop to `claude-sonnet-4-6`. Quality drops noticeably on edge cases (debut fighters, weight-class jumps).

---

## Caching strategy

Agent reports are deterministic per fighter snapshot. Cache key:

```
(fighter_name, agent_name, dossier.last_fight_date, opponent_name)
```

Invalidate when the fighter has a new fight. The opponent dimension matters because `matchup_notes_vs_opponent` differs per matchup; `effective_vs_archetypes` and the rest don't.

Tip: cache the **opponent-agnostic** fields (everything except `matchup_notes_vs_opponent` and `opponent`) keyed by `(fighter, agent, last_fight_date)`. Then the matchup block is a small per-fight delta. Cuts ~80% of token cost in fight-week iteration.

---

## Cost estimate

Per fight, single uncached run:
- 20 calls × ~3K output tokens × Opus pricing
- ≈ $0.40–$0.80 per fight on Opus 4.7
- ≈ $0.08–$0.15 on Sonnet 4.6

With caching during fight-week iteration (when the same card is re-analyzed daily as new info comes in), marginal cost approaches zero — only `matchup_notes_vs_opponent` re-runs.

---

## Integration with `ufc-11/backend/analysis_runner.py`

Current state: one generalist Claude call per fight.

Suggested refactor:

```python
# analysis_runner.py — sketch

async def analyze_fight(fighter_a, fighter_b):
    # 1. Fetch dossiers (existing scrapers)
    dossier_a = await scrape_ufc_fighter(fighter_a)
    dossier_b = await scrape_ufc_fighter(fighter_b)

    # 2. Fan out 20 specialist agent calls (new)
    reports = await run_all_agents(dossier_a, dossier_b)

    # 3. Synthesize (replace existing single call)
    prediction = await aggregate_into_prediction(reports, dossier_a, dossier_b)

    return {
        "fighter_a_reports": reports.filter(primary=fighter_a),
        "fighter_b_reports": reports.filter(primary=fighter_b),
        "prediction": prediction,
    }
```

The site can render the 20 reports as expandable per-domain cards, with the aggregator output as the headline.

---

## Sanity checks before going live

1. **Frontmatter parses** — load each `.agent.md`, parse the YAML between `---` markers, confirm `name`, `description`, `model` all present.
2. **Smoke test 1 agent** — invoke `ufc-striking-offense` with a known fighter dossier (e.g. Israel Adesanya, opponent Alex Pereira). Confirm the JSON parses and contains every required schema field.
3. **Diversity check** — run all 5 offense agents on the same fighter. The 5 reports must read distinctly. If any two read interchangeably, the prompt for that pair needs sharpening.
4. **Mirror check** — run `ufc-striking-offense` and `ufc-striking-defense` on the same fighter. They must analyze different aspects (output vs durability, attack footwork vs evasion footwork). No overlap.
5. **Matchup specificity** — invoke any offense agent with `(primary, opponent)`. The `matchup_notes_vs_opponent` block must reference the opponent **by name and concrete tendencies**, not generic content.
6. **Confidence calibration** — invoke an agent on a fighter with a thin dossier. Confidence should drop, `data_caveats` should populate. If confidence stays "high" with thin data, the prompt is over-confident — sharpen the data caveats section.

---

## Ownership / contribution

If you find a category boundary that's getting blurred (e.g. `ufc-wrestling-offense` and `ufc-takedown-offense` start saying the same things), tighten the **Validation before emitting** checklist at the bottom of each agent file. The boundary text in each agent's "Role" section is the source of truth — keep that crisp.

If you coin a new archetype that comes up repeatedly, add it to `_shared/archetype-taxonomy.md` with a one-line definition.
