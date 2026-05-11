# Data Contract — Fighter Dossier

What the calling bot must provide alongside the fighter name when invoking any of the 10 UFC agents. Most fields are already produced by `ufc-11/backend/tools/scrape_ufc_fighter.py` against ufcstats.com.

If the agent is invoked with a missing-or-thin dossier (debut fighter, regional fighter, layoff), it must lower its `confidence` field and explain in `data_caveats`. Agents must never fabricate stats.

---

## Required fields per fighter

```json
{
  "name": "Israel Adesanya",
  "record": { "wins": 24, "losses": 4, "draws": 0 },
  "dob": "1989-07-22",
  "height_in": 76,
  "reach_in": 80,
  "stance": "Switch",
  "weight_class": "Middleweight",

  "striking_stats": {
    "SLpM": 4.21,                    // significant strikes landed per minute
    "SApM": 2.97,                    // significant strikes absorbed per minute
    "str_acc": 0.50,                 // significant strike accuracy
    "str_def": 0.62,                 // significant strike defense
    "knockdown_avg": 0.78            // knockdowns per 15 min
  },

  "grappling_stats": {
    "td_avg": 0.00,                  // takedowns landed per 15 min
    "td_acc": 0.0,                   // takedown accuracy
    "td_def": 0.79,                  // takedown defense %
    "sub_avg": 0.0                   // submission attempts per 15 min
  },

  "last_5_fights": [
    {
      "date": "2023-09-09",
      "opponent": "Sean Strickland",
      "result": "L",
      "method": "Decision - Unanimous",
      "round": 5,
      "time": "5:00"
    }
    // ... up to 5
  ],

  "notable_wins": ["Robert Whittaker (x2)", "Anderson Silva", "Alex Pereira (UFC 287)"],
  "notable_losses": ["Alex Pereira (UFC 281)", "Jan Blachowicz (LHW)", "Sean Strickland"],
  "last_fight_date": "2023-09-09"
}
```

---

## Optional fields (improve confidence when present)

```json
{
  "camp": "City Kickboxing",
  "head_coach": "Eugene Bareman",
  "recent_footage_notes": "In camp footage shows increased calf-kick volume and more body work; cardio looks improved post-Strickland.",
  "weight_class_history": [
    { "class": "Light Heavyweight", "fights": 1, "record": "0-1" },
    { "class": "Middleweight", "fights": 14, "record": "11-3" }
  ],
  "ufcstats_url": "http://ufcstats.com/fighter-details/...",
  "tapology_url": "https://www.tapology.com/fighters/..."
}
```

---

## When fields are missing

| Missing field | Agent behavior |
|---|---|
| `striking_stats` | Striking-offense and striking-defense agents drop `confidence` to `medium` or `low`; cannot fill `key_stats_cited`; must reason from fight history alone |
| `grappling_stats` | Wrestling/takedown/grappling/submission agents drop `confidence`; reason from `last_5_fights` methods (e.g. "TKO/SUB from top" implies grappling) |
| `last_5_fights` | All agents drop to `confidence: low`; reasoning is mostly archetypal, not evidence-based |
| `dob` | Cardio/durability assessments must say "age unknown — caveat applies" |
| `reach_in`, `height_in` | Striking range analysis must be qualified |
| `notable_wins/losses` | Skip the level-of-competition framing |

**Hard rule:** if `record` is missing, the agent should refuse and return:
```json
{ "error": "missing required field: record", "agent": "ufc-...", "fighter": "..." }
```

---

## When the opponent is provided

The calling bot may pass an `opponent_dossier` with the same shape. When present:

- The agent fills `matchup_notes_vs_opponent` with **specific** notes referencing the opponent (e.g. "Pereira's left hook lands on retreating right hand — Adesanya tends to circle right").
- Without an opponent dossier but with `opponent` name, the agent fills `matchup_notes_vs_opponent` based on what it can recall about that opponent and lowers confidence in that section.
- Without `opponent` at all, the agent omits `matchup_notes_vs_opponent` entirely (or sets it to `null`).

---

## Notes for the calling bot

- Dossiers are cheap to fetch once; cache by fighter and invalidate on `last_fight_date` change.
- The dossier shape above is also what `ufc-11/backend/tools/scrape_ufc_fighter.py` returns (modulo field renaming) — minimal adapter work to wire up.
- For non-UFC fighters, fall back to `scrape_tapology.py` and `scrape_debut_fighter.py`; expect lower confidence.
