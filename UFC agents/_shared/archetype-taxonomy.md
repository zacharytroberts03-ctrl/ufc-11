# Archetype Taxonomy

Shared lexicon for all 10 UFC agents. When an agent fills `effective_vs_archetypes` or `vulnerable_to_archetypes` in its report, it must pick from this list (or coin a new one with a one-line definition). Keeping the language uniform lets the site stitch reports together across agents and across fights.

---

## Striking Archetypes

| Archetype | Definition |
|---|---|
| **rangy power kickboxer** | Long fighter, fights at distance, picks shots, high power per strike, lower volume. (e.g. Israel Adesanya, Alex Pereira) |
| **high-volume volume striker** | Throws constantly, accumulates damage by output, lower power per shot. (e.g. Max Holloway, Dustin Poirier) |
| **low-output counter-striker** | Patient, waits for opponent to lead, punishes mistakes, low output by design. (e.g. Anderson Silva prime, Lyoto Machida) |
| **pressure boxer** | Forward pressure, cuts the cage, boxing-heavy, breaks opponents over rounds. (e.g. Dustin Poirier, Justin Gaethje late career) |
| **sniper / distance kicker** | Picks shots from outside, kick-heavy, retreats on entries. (e.g. Edson Barboza, Stephen Thompson) |
| **southpaw counter** | Left-handed stance, builds offense around the cross and reactive counters. (e.g. Conor McGregor, Anderson Silva) |
| **switch-stance technician** | Comfortable in both stances, switches mid-combination to create angles. (e.g. T.J. Dillashaw, Henry Cejudo) |
| **brawler** | Pure forward pressure, durability-based, throws bombs, low defense. (e.g. Diego Sanchez, Justin Gaethje early) |
| **point-fighter** | Karate-base in-and-out, hit-and-not-be-hit, accumulates by control time at range. (e.g. early Stephen Thompson) |
| **leg-kick specialist** | Calf and inside leg kicks as primary weapon, cripples opponent's base over time. (e.g. Edson Barboza, Sean O'Malley) |

---

## Wrestling Archetypes

| Archetype | Definition |
|---|---|
| **collegiate-base shot wrestler** | NCAA Division 1 background, level changes, doubles, singles, chain wrestling. (e.g. Khabib Nurmagomedov, Henry Cejudo) |
| **freestyle / throws specialist** | International freestyle, lateral drops, suplexes, upper-body throws. (e.g. Khabib in scrambles, Yoel Romero) |
| **judo-base trip artist** | Clinch-heavy, grip fighting, foot sweeps, hip throws. (e.g. Karo Parisyan, Ronda Rousey) |
| **sambo grinder** | Russian sambo base, top-pressure, leg attacks, control-time grinder. (e.g. Khabib, Islam Makhachev) |
| **defensive-only wrestler** | Wrestles only to stay on feet, no offensive takedown game. (e.g. Israel Adesanya, Stephen Thompson) |
| **clinch wrestler** | Operates in the clinch, dirty boxing, knees, body locks, Greco influence. (e.g. Randy Couture, Daniel Cormier) |
| **scrambler** | Doesn't dominate position but wins mat returns and re-shots. (e.g. Frankie Edgar, Beneil Dariush) |
| **anti-wrestler** | Specialized in stuffing shots and disengaging, no ground game offense. |

---

## Grappling Archetypes (post-takedown ground game)

| Archetype | Definition |
|---|---|
| **top-control grinder** | Holds top, advances slowly, scores with control time and minimal damage risk. (e.g. Khabib, Colby Covington) |
| **BJJ scrambler** | Gi-influenced ground game, scrambles, sweeps, advances rapidly. (e.g. Demian Maia, Charles Oliveira) |
| **leglock specialist** | Heel hooks, kneebars, ankle locks; modern no-gi influence. (e.g. Ryan Hall, Garry Tonon) |
| **half-guard sweeper** | Lockdown, deep half, sweeps from bottom into top. |
| **top GnP striker** | Wins from top via ground-and-pound rather than position. (e.g. Cain Velasquez, Jon Jones) |
| **anti-grappler** | Survives bottom, gets back up, doesn't engage submissions. (e.g. Israel Adesanya bottom game) |
| **jiu-jitsu black-belt finisher** | World-class submission game, hunts finishes from any position. (e.g. Charles Oliveira, Demian Maia) |

---

## Submission Archetypes

| Archetype | Definition |
|---|---|
| **front-headlock specialist** | Anaconda, D'Arce, guillotine attacks from front headlock. (e.g. Charles Oliveira, Brian Ortega) |
| **back-take artist** | Hunts the back, RNCs from any position. (e.g. Demian Maia, Khabib) |
| **leglock hunter** | Heel hooks, kneebars, ankle locks. (e.g. Ryan Hall) |
| **guillotine threat** | Specifically guillotines off failed shots and scrambles. (e.g. Brian Ortega) |
| **kimura / armbar grinder** | Joint-lock hunter from top control. |
| **submission counter-striker** | Lures opponent into bad position, traps in submission. |
| **positional submitter** | Uses dominant position to lock in submissions, low risk. |

---

## How agents use this

1. **Identify primary archetype** for the fighter being scouted (one or two)
2. **List effective-vs archetypes** — opponent types this fighter beats up in the agent's category
3. **List vulnerable-to archetypes** — opponent types that exploit this fighter's gaps in the agent's category
4. **Map the named opponent** (when provided) to one of these archetypes for the `matchup_notes_vs_opponent` block

If no archetype fits, an agent may coin a new one — but should write a one-line definition inline. Future versions of this taxonomy will absorb commonly coined archetypes.
