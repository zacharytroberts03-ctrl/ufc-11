// Win probability ↔ American moneyline odds.
//
// Conversion formula:
//   p >= 0.5  →  odds = round(-100 * p / (1 - p))   // negative (favorite)
//   p <  0.5  →  odds = round( 100 * (1 - p) / p)   // positive (underdog)
//
// Examples:
//   p=0.50  →  ±100
//   p=0.60  →  -150
//   p=0.84  →  -525
//   p=0.40  →  +150
//   p=0.20  →  +400

export function probToAmericanOdds(prob: number | null | undefined): number | null {
  if (prob == null || prob <= 0 || prob >= 1) return null;
  if (prob >= 0.5) return Math.round((-100 * prob) / (1 - prob));
  return Math.round((100 * (1 - prob)) / prob);
}

export function formatAmericanOdds(odds: number | null | undefined): string {
  if (odds == null) return "—";
  return odds > 0 ? `+${odds}` : String(odds);
}
