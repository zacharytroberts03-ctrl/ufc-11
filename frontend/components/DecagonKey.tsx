import { AXES } from "./FighterDecagon";

const OFFENSE = AXES.filter((a) => a.short.startsWith("O-"));
const DEFENSE = AXES.filter((a) => a.short.startsWith("D-"));

interface Props {
  side: "offense" | "defense";
}

function Row({ short, full, color }: { short: string; full: string; color: string }) {
  return (
    <div className="flex items-baseline gap-2 min-w-0">
      <span className="font-black text-sm tracking-wider w-12 flex-shrink-0" style={{ color }}>
        {short}
      </span>
      <span className="text-sm text-ufc-muted min-w-0 flex-1">{full}</span>
    </div>
  );
}

export default function DecagonKey({ side }: Props) {
  const isOffense = side === "offense";
  const items = isOffense ? OFFENSE : DEFENSE;
  const heading = isOffense ? "Offense" : "Defense";
  const accent = isOffense ? "#dc0000" : "#d4af37";
  const stripSuffix = isOffense ? " Offense" : " Defense";

  return (
    <aside
      className="rounded-xl p-4 sm:p-5 w-full flex flex-col"
      style={{
        background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
        border: "1px solid #2a2a2a",
      }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[11px] font-black tracking-[0.25em] uppercase" style={{ color: accent }}>
          {heading}
        </h3>
        <span className="text-[10px] text-ufc-muted">1–10</span>
      </div>
      <div className="flex flex-col justify-around flex-1 gap-1">
        {items.map((a) => (
          <Row
            key={a.short}
            short={a.short}
            full={a.full.replace(stripSuffix, "")}
            color={accent}
          />
        ))}
      </div>
    </aside>
  );
}
