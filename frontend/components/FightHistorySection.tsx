import type { FighterData } from "@/lib/types";

interface FightHistoryEntry {
  result?: string;
  opponent?: string;
  method?: string;
  round?: string | number | null;
  time?: string;
  date?: string;
}

function resultClass(result?: string): string {
  const r = (result || "").toUpperCase();
  if (r.startsWith("W")) return "text-ufc-green";
  if (r.startsWith("L")) return "text-ufc-red";
  return "text-ufc-muted";
}

function resultLabel(result?: string): string {
  const r = (result || "").toUpperCase();
  if (r.startsWith("W")) return "W";
  if (r.startsWith("L")) return "L";
  if (r.startsWith("D")) return "D";
  if (r.startsWith("N")) return "NC";
  return "?";
}

function FightRow({ entry }: { entry: FightHistoryEntry }) {
  const round = entry.round ? `R${entry.round}` : "—";
  const time = entry.time && entry.time !== "0:00" ? entry.time : "";
  const roundTime = time ? `${round} · ${time}` : round;

  return (
    <tr className="border-t border-ufc-border/40">
      <td className={`py-2 pr-2 font-black text-sm ${resultClass(entry.result)}`}>
        {resultLabel(entry.result)}
      </td>
      <td className="py-2 pr-2 text-white text-xs sm:text-sm font-semibold">
        {entry.opponent || "—"}
      </td>
      <td className="py-2 pr-2 text-ufc-muted text-[11px] sm:text-xs whitespace-nowrap">
        {entry.method || "—"}
      </td>
      <td className="py-2 pr-2 text-ufc-muted text-[11px] sm:text-xs whitespace-nowrap">
        {roundTime}
      </td>
      <td className="py-2 text-ufc-muted text-[11px] sm:text-xs whitespace-nowrap">
        {entry.date || "—"}
      </td>
    </tr>
  );
}

function FighterColumn({
  name,
  data,
  debut,
}: {
  name: string;
  data?: FighterData | null;
  debut?: boolean;
}) {
  const history = ((data?.fight_history as FightHistoryEntry[] | undefined) || []).slice(0, 5);

  return (
    <div className="rounded-lg border border-ufc-border/40 bg-black/20 p-3 sm:p-4">
      <h4 className="font-black text-sm sm:text-base text-white mb-2 sm:mb-3">{name}</h4>
      {debut ? (
        <p className="text-xs sm:text-sm text-ufc-muted italic">
          Making their UFC debut — no prior UFC fights on record.
        </p>
      ) : history.length === 0 ? (
        <p className="text-xs sm:text-sm text-ufc-muted italic">No fight history available.</p>
      ) : (
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="text-[10px] sm:text-[11px] uppercase tracking-wider text-ufc-muted">
              <th className="pb-1 pr-2 font-bold">Res</th>
              <th className="pb-1 pr-2 font-bold">Opponent</th>
              <th className="pb-1 pr-2 font-bold">Method</th>
              <th className="pb-1 pr-2 font-bold">R · Time</th>
              <th className="pb-1 font-bold">Date</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry, i) => (
              <FightRow key={i} entry={entry} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

interface Props {
  f1Name: string;
  f2Name: string;
  f1Data?: FighterData | null;
  f2Data?: FighterData | null;
  f1Debut?: boolean;
  f2Debut?: boolean;
}

export default function FightHistorySection({
  f1Name,
  f2Name,
  f1Data,
  f2Data,
  f1Debut,
  f2Debut,
}: Props) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <FighterColumn name={f1Name} data={f1Data} debut={f1Debut} />
      <FighterColumn name={f2Name} data={f2Data} debut={f2Debut} />
    </div>
  );
}
