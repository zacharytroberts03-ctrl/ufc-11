import { AXES } from "./FighterDecagon";

// Splits the 10 axes into offense (O- prefix) and defense (D- prefix) columns.
const OFFENSE = AXES.filter((a) => a.short.startsWith("O-"));
const DEFENSE = AXES.filter((a) => a.short.startsWith("D-"));

function Row({ short, full }: { short: string; full: string }) {
  return (
    <div className="flex items-baseline gap-3 py-1">
      <span className="font-black text-ufc-red text-xs tracking-wider w-14 flex-shrink-0">
        {short}
      </span>
      <span className="text-xs text-ufc-muted">{full}</span>
    </div>
  );
}

export default function DecagonKey() {
  return (
    <aside
      className="rounded-xl p-4 sm:p-5 mb-6"
      style={{
        background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
        border: "1px solid #2a2a2a",
      }}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[11px] font-black tracking-[0.25em] text-white uppercase">
          Chart Key
        </h3>
        <span className="text-[10px] text-ufc-muted">10 specialist agents · 1–10 scale</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
        <div>
          <div className="text-[10px] font-black tracking-widest text-ufc-red mb-1.5 uppercase">
            Offense
          </div>
          {OFFENSE.map((a) => (
            <Row key={a.short} short={a.short} full={a.full.replace(" Offense", "")} />
          ))}
        </div>
        <div>
          <div className="text-[10px] font-black tracking-widest mb-1.5 uppercase" style={{ color: "#d4af37" }}>
            Defense
          </div>
          {DEFENSE.map((a) => (
            <Row key={a.short} short={a.short} full={a.full.replace(" Defense", "")} />
          ))}
        </div>
      </div>
    </aside>
  );
}
