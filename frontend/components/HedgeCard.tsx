import type { HedgeSummary } from "@/lib/types";

function fmtOdds(odds: number) {
  return odds > 0 ? `+${odds}` : String(odds);
}

interface Props {
  hedge: HedgeSummary;
}

export default function HedgeCard({ hedge }: Props) {
  if (!hedge.arb_exists) return null;

  return (
    <div className="card overflow-hidden mb-6">
      <div className="px-5 py-3 border-b border-ufc-border bg-ufc-green/5 flex items-center gap-2">
        <svg className="w-4 h-4 text-ufc-green" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
        </svg>
        <h3 className="text-sm font-bold text-ufc-green uppercase tracking-wider">
          Hedge Betting Instructions
        </h3>
      </div>

      <div className="p-5 space-y-3">
        {/* Bet 1 */}
        <div className="flex items-center justify-between py-3 border-b border-ufc-border/50">
          <div>
            <span className="font-bold text-ufc-text">{hedge.f1_name}</span>
            <span className="text-ufc-muted text-sm ml-2">
              on {hedge.f1_book}{" "}
              <span className={hedge.f1_odds > 0 ? "text-ufc-green" : "text-ufc-red"}>
                ({fmtOdds(hedge.f1_odds)})
              </span>
            </span>
          </div>
          <span className="text-ufc-text font-black text-lg">
            ${hedge.f1_stake.toFixed(2)}
          </span>
        </div>

        {/* Bet 2 */}
        <div className="flex items-center justify-between py-3 border-b border-ufc-border/50">
          <div>
            <span className="font-bold text-ufc-text">{hedge.f2_name}</span>
            <span className="text-ufc-muted text-sm ml-2">
              on {hedge.f2_book}{" "}
              <span className={hedge.f2_odds > 0 ? "text-ufc-green" : "text-ufc-red"}>
                ({fmtOdds(hedge.f2_odds)})
              </span>
            </span>
          </div>
          <span className="text-ufc-text font-black text-lg">
            ${hedge.f2_stake.toFixed(2)}
          </span>
        </div>

        {/* Profit */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-ufc-muted text-sm">Guaranteed Profit</span>
          <div className="text-right">
            <span className="text-ufc-green font-black text-xl">
              ${hedge.guaranteed_profit.toFixed(2)}
            </span>
            <span className="text-ufc-muted text-xs ml-2">
              ({hedge.roi_pct.toFixed(2)}% ROI)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
