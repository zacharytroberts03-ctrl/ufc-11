import { resolvePhotoUrl } from "@/lib/photoUrl";
import { flagSvgUrlFromCountry, flagSvgUrlFromLocation } from "@/lib/flagEmoji";
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

function FlagImg({ src, alt }: { src: string; alt: string }) {
  /* eslint-disable-next-line @next/next/no-img-element */
  return (
    <img
      src={src}
      alt={alt}
      className="inline-block w-4 h-3 align-[-2px] rounded-[1px]"
      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
    />
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

  const lines: { label: string; value: string; flagSrc?: string | null }[] = [];
  if (i.nationality) {
    lines.push({
      label: "From",
      value: i.nationality,
      flagSrc: flagSvgUrlFromCountry(i.nationality),
    });
  }
  if (i.fights_out_of) {
    lines.push({
      label: "Fighting Out of",
      value: i.fights_out_of,
      flagSrc: flagSvgUrlFromLocation(i.fights_out_of),
    });
  }
  if (i.camp) {
    lines.push({ label: "Team", value: i.camp });
  }
  if (!lines.length) return null;

  return (
    <div className={`flex flex-col gap-1 mt-2 w-full ${align === "right" ? "items-end" : "items-start"}`}>
      {lines.map((line, idx) => (
        <div
          key={idx}
          className={`text-xs text-white leading-snug ${align === "right" ? "text-right" : "text-left"}`}
        >
          {line.label} {line.value}
          {line.flagSrc && (
            <>
              {" "}
              <FlagImg src={line.flagSrc} alt="" />
            </>
          )}
        </div>
      ))}
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
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-6 md:gap-4 md:items-start">
        {/* F1 side: photo+name + decagon on top, details row below */}
        <div className="flex flex-col gap-3 min-w-0">
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
          <FighterDetails data={f1Data} align="left" />
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

        {/* F2 side: decagon + photo+name on top, details row below (mirrored) */}
        <div className="flex flex-col gap-3 min-w-0">
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
            </div>
          </div>
          <FighterDetails data={f2Data} align="right" />
        </div>
      </div>
    </div>
  );
}
