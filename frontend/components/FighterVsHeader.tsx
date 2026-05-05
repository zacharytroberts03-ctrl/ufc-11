import { resolvePhotoUrl } from "@/lib/photoUrl";
import { flagEmojiFromCountry, flagEmojiFromLocation } from "@/lib/flagEmoji";
import FighterDecagon from "./FighterDecagon";
import type { AnalysisResult, FighterData } from "@/lib/types";

const F1_COLOR = "#dc0000";  // UFC red
const F2_COLOR = "#d4af37";  // UFC gold

interface Props {
  f1Name: string;
  f2Name: string;
  f1Img?: string | null;
  f2Img?: string | null;
  f1Debut?: boolean;
  f2Debut?: boolean;
  f1Data?: FighterData;
  f2Data?: FighterData;
  specialistReports?: AnalysisResult["specialist_reports"];
}

function FighterPhoto({
  name,
  img,
  borderColor,
}: {
  name: string;
  img: string | null;
  borderColor: string;
}) {
  return (
    <div className="relative">
      {img && (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img
          src={img}
          alt={name}
          className="w-20 h-20 sm:w-24 sm:h-24 rounded-full object-cover shadow-lg"
          style={{ border: `3px solid ${borderColor}` }}
          onError={(e) => {
            const el = e.target as HTMLImageElement;
            el.style.display = "none";
            el.nextElementSibling?.removeAttribute("style");
          }}
        />
      )}
      <div
        className="w-20 h-20 sm:w-24 sm:h-24 rounded-full flex items-center justify-center text-3xl sm:text-4xl font-black"
        style={{
          display: img ? "none" : "flex",
          backgroundColor: "#1a1a1a",
          border: `3px solid ${borderColor}`,
          color: borderColor,
        }}
      >
        {name[0]}
      </div>
    </div>
  );
}

function InfoLine({
  flag,
  label,
  value,
  align,
}: {
  flag?: string | null;
  label: string;
  value: string;
  align: "left" | "right";
}) {
  const items = [
    flag ? <span key="flag" className="text-base leading-none">{flag}</span> : null,
    <span key="label" className="text-[10px] uppercase tracking-widest text-ufc-muted">{label}</span>,
    <span key="value" className="text-xs text-white truncate">{value}</span>,
  ];
  return (
    <div className={`flex items-center gap-1.5 max-w-full ${align === "right" ? "justify-end" : "justify-start"}`}>
      {align === "right" ? items.slice().reverse() : items}
    </div>
  );
}

function FighterDetails({
  data,
  align,
}: {
  data?: FighterData;
  align: "left" | "right";
}) {
  const i = data?.intangibles;
  if (!i) return null;
  const nationality = i.nationality || undefined;
  const fightsOutOf = i.fights_out_of || undefined;
  const camp = i.camp || undefined;

  if (!nationality && !fightsOutOf && !camp) return null;

  return (
    <div className={`flex flex-col gap-1 mt-1 w-full ${align === "right" ? "items-end" : "items-start"}`}>
      {nationality && (
        <InfoLine
          flag={flagEmojiFromCountry(nationality)}
          label="From"
          value={nationality}
          align={align}
        />
      )}
      {fightsOutOf && (
        <InfoLine
          flag={flagEmojiFromLocation(fightsOutOf)}
          label="Out of"
          value={fightsOutOf}
          align={align}
        />
      )}
      {camp && (
        <InfoLine
          label="Camp"
          value={camp}
          align={align}
        />
      )}
    </div>
  );
}

export default function FighterVsHeader({
  f1Name,
  f2Name,
  f1Img,
  f2Img,
  f1Debut,
  f2Debut,
  f1Data,
  f2Data,
  specialistReports,
}: Props) {
  const f1Photo = resolvePhotoUrl(f1Img, f1Name);
  const f2Photo = resolvePhotoUrl(f2Img, f2Name);

  return (
    <div
      className="rounded-xl p-5 sm:p-7 mb-6 shadow-2xl"
      style={{
        background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
        border: "2px solid #dc0000",
      }}
    >
      {/* Desktop: two columns with VS in middle. Mobile: stack. */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 md:gap-4 items-center">
        {/* F1 side: photo + name + details on left, decagon on right */}
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="flex flex-col items-center gap-2 sm:items-start min-w-0 max-w-[12rem]">
            <FighterPhoto name={f1Name} img={f1Photo} borderColor={F1_COLOR} />
            {f1Debut && (
              <span className="text-[10px] font-black tracking-widest uppercase px-2 py-0.5 rounded"
                    style={{ backgroundColor: F1_COLOR, color: "#fff" }}>
                UFC DEBUT
              </span>
            )}
            <h2 className="text-lg sm:text-xl font-black text-white text-center sm:text-left leading-tight max-w-[12rem]">
              {f1Name}
            </h2>
            <FighterDetails data={f1Data} align="left" />
          </div>
          <div className="flex-shrink-0">
            <FighterDecagon
              reports={specialistReports}
              fighterName={f1Name}
              color={F1_COLOR}
              size={175}
            />
          </div>
        </div>

        {/* VS divider */}
        <div className="flex items-center justify-center md:flex-col">
          <div className="hidden md:block h-24 w-px bg-gradient-to-b from-transparent via-[#dc0000] to-transparent" />
          <span
            className="text-3xl sm:text-4xl font-black tracking-[0.2em] my-3"
            style={{ color: F1_COLOR }}
          >
            VS
          </span>
          <div className="hidden md:block h-24 w-px bg-gradient-to-b from-transparent via-[#d4af37] to-transparent" />
        </div>

        {/* F2 side: decagon on left, photo + name + details on right (mirrored) */}
        <div className="flex flex-col-reverse sm:flex-row items-center gap-4 md:justify-end">
          <div className="flex-shrink-0">
            <FighterDecagon
              reports={specialistReports}
              fighterName={f2Name}
              color={F2_COLOR}
              size={175}
            />
          </div>
          <div className="flex flex-col items-center gap-2 sm:items-end min-w-0 max-w-[12rem]">
            <FighterPhoto name={f2Name} img={f2Photo} borderColor={F2_COLOR} />
            {f2Debut && (
              <span className="text-[10px] font-black tracking-widest uppercase px-2 py-0.5 rounded"
                    style={{ backgroundColor: F2_COLOR, color: "#1a1a1a" }}>
                UFC DEBUT
              </span>
            )}
            <h2 className="text-lg sm:text-xl font-black text-white text-center sm:text-right leading-tight max-w-[12rem]">
              {f2Name}
            </h2>
            <FighterDetails data={f2Data} align="right" />
          </div>
        </div>
      </div>
    </div>
  );
}
