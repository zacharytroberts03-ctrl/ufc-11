import type { BetsObject } from "@/lib/types";
import { probToAmericanOdds, formatAmericanOdds } from "@/lib/odds";

interface Props {
  bets?: BetsObject;
}

export default function FavoriteFighterPanel({ bets }: Props) {
  const ml = bets?.moneyline;
  if (!ml?.pick || ml.win_prob == null) {
    return (
      <p className="text-sm text-ufc-muted">
        No pick available — analysis hasn&apos;t run yet for this fight.
      </p>
    );
  }

  const winPct = Math.round(ml.win_prob * 100);
  const odds = probToAmericanOdds(ml.win_prob);
  const oddsStr = formatAmericanOdds(odds);

  return (
    <div className="space-y-4">
      {/* Pick + win probability */}
      <div className="flex items-center gap-3">
        <span className="text-3xl">🏆</span>
        <div>
          <div className="text-xl sm:text-2xl font-black text-white leading-tight">
            {ml.pick}
          </div>
          <div className="text-sm text-ufc-muted mt-0.5">
            {winPct}% win probability
          </div>
        </div>
      </div>

      {/* Calculated odds + confidence */}
      <div className="flex items-center justify-between rounded-lg p-4 bg-black/40 border border-ufc-green/30">
        <div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-ufc-muted mb-1">
            Calculated Odds
          </div>
          <div
            className={`text-3xl font-black ${odds !== null && odds < 0 ? "text-ufc-green" : "text-white"}`}
          >
            {oddsStr}
          </div>
        </div>
        {ml.confidence && (
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-[0.2em] text-ufc-muted mb-1">
              Confidence
            </div>
            <div className="text-sm font-bold uppercase text-white">
              {ml.confidence}
            </div>
          </div>
        )}
      </div>

      {/* Key thesis (one-line reasoning) */}
      {ml.key_thesis && (
        <p className="text-sm text-white/80 italic">{ml.key_thesis}</p>
      )}

      {/* Disclaimer — these odds are computed by us, not pulled from any sportsbook */}
      <div className="text-xs text-ufc-muted leading-relaxed border-l-2 border-ufc-border pl-3">
        Based on the {winPct}% win chance we determined, the moneyline odds for{" "}
        <span className="text-white font-semibold">{ml.pick}</span> should be around{" "}
        <span className="text-white font-semibold">{oddsStr}</span>. We are not pulling
        fighter odds from any sportsbook — these are calculated independently from our
        own analysis. Use this as a benchmark when shopping the lines: better odds than{" "}
        {oddsStr} on {ml.pick} at a sportsbook means you&apos;re getting value.
      </div>
    </div>
  );
}
