# Output Schema

Every one of the 10 UFC agents emits a report with the **same JSON shape** plus a markdown narrative. Only `agent` and the keys inside `sub_ratings` differ between agents.

Agents output the JSON inside a fenced ```json block, then follow it with the markdown narrative. The calling bot can parse the JSON directly and surface the narrative in the UI.

---

## JSON Schema (every agent emits this shape)

```json
{
  "agent": "ufc-striking-offense",
  "fighter": "Israel Adesanya",
  "opponent": "Alex Pereira",

  "rating_1_to_10": 9,

  "sub_ratings": {
    // 4–6 keys, agent-specific (see each agent file for its keys)
    "power": 8,
    "volume": 7,
    "accuracy": 9,
    "combinations": 8,
    "footwork_to_attack": 9
  },

  "strengths": [
    "Lead-hand jab and lead-hand hook on the entry",
    "Calf-kick targeting at distance",
    "Counter-left-hook off the lead-leg check"
  ],

  "weaknesses": [
    "Output drops in championship rounds vs pressure",
    "Predictable circle-right pattern when hurt"
  ],

  "signature_techniques": [
    "Lead-hand jab",
    "Lead calf kick",
    "Switch-stance lead-leg side kick",
    "Counter left hook off check"
  ],

  "effective_vs_archetypes": [
    {
      "archetype": "low-output counter-strikers",
      "why": "Adesanya's volume and feinting force counter-strikers to commit, opening up his picks."
    },
    {
      "archetype": "leg-kick specialists",
      "why": "His distance management and stance switches neutralize calf-kick rhythm."
    }
  ],

  "vulnerable_to_archetypes": [
    {
      "archetype": "rangy power kickboxer",
      "why": "Equal reach with more single-shot power forces him to retreat into the cage where his footwork shrinks."
    },
    {
      "archetype": "pressure boxer",
      "why": "Walked-down by Strickland; his output drops materially when he can't reset distance."
    }
  ],

  "matchup_notes_vs_opponent": {
    "opponent_archetype": "rangy power kickboxer",
    "exploitable": [
      "Pereira's slow right hand on the entry — counterable with the lead-hand hook",
      "Pereira's defensive footwork going right is weaker"
    ],
    "must_avoid": [
      "Trading in the pocket; Pereira's left hook is the cleaner finish",
      "Letting Pereira step in unopposed — he builds output as the fight ages"
    ],
    "x_factors": [
      "Adesanya's calf kicks compounding by round 3",
      "Adesanya's feint volume to short-circuit Pereira's left-hook timing"
    ]
  },

  "recent_trend": "stable",
  "trend_evidence": "Last 3 fights: lost to Strickland (decision), beat Pereira (KO2), lost to Pereira (KO5). Striking accuracy and SLpM steady; output drops late are the only consistent dip.",

  "cardio_factor": "Holds output through round 3 well; rounds 4–5 see a measurable volume drop especially under pressure.",
  "durability_factor": "Solid chin historically — has been finished only by Pereira's specific left-hook setup (twice).",

  "camp_and_coaching_notes": "City Kickboxing — Bareman emphasizes feint-heavy, footwork-first striking. Camp typically peaks technique, occasionally undertrains backwards-pressure scenarios.",

  "key_stats_cited": [
    { "stat": "SLpM",       "value": 4.21,  "source": "ufcstats.com" },
    { "stat": "str_acc",    "value": 0.50,  "source": "ufcstats.com" },
    { "stat": "str_def",    "value": 0.62,  "source": "ufcstats.com" },
    { "stat": "reach_in",   "value": 80,    "source": "ufcstats.com" }
  ],

  "confidence": "high",
  "data_caveats": []
}
```

---

## Field Reference

| Field | Type | Required | Notes |
|---|---|---|---|
| `agent` | string | yes | Must equal the agent's filename (e.g. `ufc-striking-offense`) |
| `fighter` | string | yes | Primary fighter being scouted |
| `opponent` | string \| null | yes | Named opponent if provided, else `null` |
| `rating_1_to_10` | integer 1–10 | yes | Overall rating in this category |
| `sub_ratings` | object | yes | 4–6 keys, integers 1–10. Keys defined per agent. |
| `strengths` | string[] | yes | 3–5 items, each one sentence |
| `weaknesses` | string[] | yes | 2–4 items, each one sentence |
| `signature_techniques` | string[] | yes | 3–6 specific techniques |
| `effective_vs_archetypes` | object[] | yes | 2–4 items; archetype + reasoning |
| `vulnerable_to_archetypes` | object[] | yes | 2–4 items; archetype + reasoning |
| `matchup_notes_vs_opponent` | object \| null | conditional | Required if `opponent` non-null |
| `recent_trend` | enum | yes | `improving` \| `declining` \| `stable` |
| `trend_evidence` | string | yes | One paragraph citing recent fights |
| `cardio_factor` | string | yes | Round-by-round assessment relevant to this category |
| `durability_factor` | string | yes | Chin / fight-ending damage tolerance |
| `camp_and_coaching_notes` | string | yes | Or `"unknown"` if absent from dossier |
| `key_stats_cited` | object[] | yes | 3–8 raw stats backing the analysis |
| `confidence` | enum | yes | `high` \| `medium` \| `low` |
| `data_caveats` | string[] | yes | Empty array if confidence = high |

---

## Markdown narrative (after the JSON)

200–400 words, plain prose, written for a fan-level reader. Order:

1. **One-line verdict** — what kind of [striker / wrestler / etc.] this fighter is, in this domain
2. **What works** — the 2-3 most important strengths, illustrated
3. **What breaks** — the 1-2 most important weaknesses, illustrated
4. **Matchup synthesis** — if opponent provided, how this fighter's game maps onto that specific opponent

The narrative humanizes the JSON. The JSON is for the site; the narrative is for users reading the analysis.

---

## Markdown narrative example (snippet)

> Adesanya in the striking-offense lens is a rangy power kickboxer who fights more like a sniper than a volume puncher. The lead hand jab and the calf kick are his metronome — they set distance and rob opponent stances. When opponents commit, he counters with a lead-hand hook off a check; that's how he beat Pereira at UFC 287. ...

---

## Validation rule for agents

Before emitting, agents should mentally check:
- [ ] All required fields present?
- [ ] `sub_ratings` has agent's documented keys?
- [ ] `effective_vs` and `vulnerable_to` archetypes drawn from `_shared/archetype-taxonomy.md` (or coined with definition)?
- [ ] `matchup_notes_vs_opponent` is non-null iff `opponent` is non-null?
- [ ] `confidence` matches the data quality? (low if dossier was thin)
- [ ] `key_stats_cited` actually appear in the dossier? (no fabrication)
