"""Manual overrides for fighter intangibles when scrape sources are incomplete.

Tapology sometimes has empty Affiliation / nationality / fights_out_of values
for less-prominent fighters. This module lets us patch those gaps
deterministically. Keys are the fighter's name as returned by
`scrape_ufc_fighter` (which mirrors UFCStats), e.g. "Waldo Cortes Acosta"
not "Waldo Cortes-Acosta".

Only fields listed here are filled in — they never overwrite a non-empty
value already returned by the scraper.

When you discover a gap:
  1. Verify the fighter's UFCStats name (look at f1_data.name / f2_data.name in
     analyses.json or check ufcstats.com directly).
  2. Add an entry below with the fields you have.
  3. The next refresh picks it up automatically; for an immediate fix, run
     scripts/refresh_intangibles.py.
"""

OVERRIDES: dict[str, dict[str, str]] = {
    "Waldo Cortes Acosta": {
        "camp": "UKF Gym",
    },
}


def apply_intangibles_overrides(fighter_name: str, intangibles: dict | None) -> dict:
    """Merge any manual overrides for this fighter into their intangibles dict.
    Manual values only fill in *missing* fields — scraped values always win."""
    out = dict(intangibles or {})
    overrides = OVERRIDES.get(fighter_name, {})
    for k, v in overrides.items():
        if not out.get(k):
            out[k] = v
    return out
