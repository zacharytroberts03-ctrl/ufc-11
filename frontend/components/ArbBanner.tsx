interface ArbProps {
  roiPct: number;
  guaranteedProfit: number;
  totalStake: number;
}

interface NoArbProps {
  bestF1Book: string;
  bestF1Odds: number;
  bestF2Book: string;
  bestF2Odds: number;
}

function fmtOdds(odds: number) {
  return odds > 0 ? `+${odds}` : String(odds);
}

export function ArbBanner({ roiPct, guaranteedProfit, totalStake }: ArbProps) {
  return (
    <div className="rounded-xl border border-ufc-green/40 bg-ufc-green/5 px-6 py-5 mb-6 animate-fade-in">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-ufc-green text-lg">✓</span>
        <span className="text-ufc-green font-black text-sm uppercase tracking-widest">
          Arbitrage Found
        </span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-ufc-muted text-xs uppercase tracking-wider mb-1">ROI</p>
          <p className="text-ufc-green font-black text-2xl">{roiPct.toFixed(2)}%</p>
        </div>
        <div>
          <p className="text-ufc-muted text-xs uppercase tracking-wider mb-1">Guaranteed Profit</p>
          <p className="text-ufc-green font-black text-2xl">${guaranteedProfit.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-ufc-muted text-xs uppercase tracking-wider mb-1">Total Stake</p>
          <p className="text-ufc-text font-black text-2xl">${totalStake.toFixed(0)}</p>
        </div>
      </div>
    </div>
  );
}

export function NoArbBanner({ bestF1Book, bestF1Odds, bestF2Book, bestF2Odds }: NoArbProps) {
  return (
    <div className="rounded-xl border border-ufc-border bg-ufc-surface px-5 py-4 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-ufc-muted text-sm">✕</span>
        <span className="text-ufc-muted font-semibold text-sm">No guaranteed arbitrage</span>
      </div>
      <p className="text-ufc-muted text-sm">
        Best available lines:{" "}
        <span className="text-ufc-text font-semibold">{bestF1Book}</span>{" "}
        <span className={bestF1Odds > 0 ? "text-ufc-green font-bold" : "text-ufc-red font-bold"}>
          {fmtOdds(bestF1Odds)}
        </span>{" "}
        &nbsp;·&nbsp;{" "}
        <span className="text-ufc-text font-semibold">{bestF2Book}</span>{" "}
        <span className={bestF2Odds > 0 ? "text-ufc-green font-bold" : "text-ufc-red font-bold"}>
          {fmtOdds(bestF2Odds)}
        </span>
      </p>
    </div>
  );
}
