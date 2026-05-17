# Lessons learned (auto-regenerated 2026-05-17T12:55:25.853829+00:00)

This file is regenerated from `lessons.json` on every reflection run.
Do not edit by hand — the merge pass will overwrite changes.

---

## Watchlist (not yet injected)

- **watch_001** () — Submission probability is systematically under-floored when one fighter has dominant top-control or active sub-hunting tools and the opponent has zero offensive grappling, no sweep history, or an untested 'black box' bottom game. Career sub_finish_rate priors collapse method probability to 2-6% when positional dominance plus a passenger bottom game is itself a base-rate submission generator. (1 obs)
- **watch_002** () — Mishandled translation between raw takedown stats (td_avg, td_acc, TDD%) and expected fight-altering outcomes. Sometimes inflates a paper wrestling edge into a 'decisive domain' when expected successful TDs are <1/fight; other times dismisses real wrestling threats by anchoring on low td_acc or 'won't shoot' priors. TDD% treated as hard number rather than noisy, opponent-dependent estimate. (1 obs)
- **watch_003** () — Synthesizer misuses closing line movement — either citing stale/incorrect movement to confirm its own pick, or fading large market consensus moves without identifying a specific reason the market is wrong. Strong adverse line movement is rationalized rather than treated as a Bayesian signal. (1 obs)
- **watch_004** () — Recent form/momentum and raw striking stats applied asymmetrically without opposition-quality adjustment. Win streaks against weaker opposition taken at face value; losing streaks against elite opposition treated as declining-trajectory penalties — leading to systematic picking of the 'hotter' fighter who had a softer recent slate. (1 obs)
- **watch_005** () — When specialist agents explicitly flag a categorical stylistic mismatch ('this is the exact test he's built to fail,' chin vs sniper, untested bottom game vs top-control wrestler), the synthesizer downweights these structural flags in favor of demographic/intangible factors (age, activity, momentum, cardio path) or multi-path narratives. (1 obs)
- **watch_006** () — Raw SLpM differential over-weighted as predictive of round-winning without accounting for clinch/cage-pressure neutralization by a forward-pressure opponent with adequate strike defense. (1 obs)
- **watch_007** () — Synthesizer leans on a single 'blueprint' fight comparison without verifying stylistic match or that the cited fight was decisive rather than a split decision. (1 obs)
- **watch_008** () — Sub_finish_rate computed from <10 attempts treated as a decisive predictor of finishing reliability, when small-sample conversion percentages are statistically meaningless and sub_avg + demonstrated recent finishes are the better signal. (1 obs)
- **watch_009** () — Multiplicative penalization of specialist skills (sub_avg, KO power, etc.) when a fighter is on a losing streak — treating 'declining confidence' as fact rather than narrative, without concrete evidence the specific skill is failing. (1 obs)
- **watch_010** () — When the underdog's primary finishing path is identified by specialists as the single coherent danger, the synthesizer still floors that method probability at 2-6% rather than at the empirical base rate for that path in similar matchups. (1 obs)

