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
          className="w-16 h-16 sm:w-24 sm:h-24 rounded-full object-cover shadow-lg"
          style={{ border: `3px solid ${borderColor}` }}
          onError={(e) => {
            const el = e.target as HTMLImageElement;
            el.style.display = "none";
            el.nextElementSibling?.removeAttribute("style");
          }}
        />
      )}
      <div
        className="w-16 h-16 sm:w-24 sm:h-24 rounded-full flex items-center justify-center text-2xl sm:text-4xl font-black"
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

function FighterDetails({ data }: { data?: FighterData }) {
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
    lines.push({ label: "Team :", value: i.camp });
  }
  if (!lines.length) return null;

  return (
    <div className="flex flex-col gap-1 mt-2 w-full items-center text-center">
      {lines.map((line, idx) => (
        <div key={idx} className="text-[11px] sm:text-xs text-white leading-snug">
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

function FighterColumn({
  name,
  photo,
  debut,
  data,
  reports,
  color,
  debutTextColor,
}: {
  name: string;
  photo: string | null;
  debut?: boolean;
  data?: FighterData;
  reports?: AnalysisResult["specialist_reports"];
  color: string;
  debutTextColor: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2 sm:gap-3 min-w-0">
      <FighterPhoto name={name} img={photo} borderColor={color} />
      {debut && (
        <span
          className="text-[9px] sm:text-[10px] font-black tracking-widest uppercase px-2 py-0.5 rounded whitespace-nowrap"
          style={{ backgroundColor: color, color: debutTextColor }}
        >
          UFC DEBUT
        </span>
      )}
      <h2 className="text-sm sm:text-lg md:text-xl font-black text-white text-center leading-tight">
        {name}
      </h2>
      <div className="w-full">
        <FighterDecagon
          reports={reports}
          fighterName={name}
          color={color}
          size={175}
        />
      </div>
      <FighterDetails data={data} />
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
      className="rounded-xl p-3 sm:p-6 mb-6 shadow-2xl"
      style={{
        background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
        border: "2px solid #dc0000",
      }}
    >
      {/* 3-column layout: F1 column | VS | F2 column.
          Each fighter is a vertical stack so the decagons end up at the same
          row position and sit directly across from each other. */}
      <div className="grid grid-cols-[1fr_auto_1fr] gap-2 sm:gap-4 items-start">
        <FighterColumn
          name={f1Name}
          photo={f1Photo}
          debut={f1Debut}
          data={f1Data}
          reports={specialistReports}
          color={F1_COLOR}
          debutTextColor="#ffffff"
        />

        {/* Vertical VS divider */}
        <div className="flex flex-col items-center justify-center self-stretch">
          <div className="flex-1 w-px bg-gradient-to-b from-transparent via-[#dc0000] to-transparent" />
          <span
            className="text-2xl sm:text-4xl md:text-5xl font-black tracking-[0.15em] my-2 sm:my-4"
            style={{ color: F1_COLOR }}
          >
            VS
          </span>
          <div className="flex-1 w-px bg-gradient-to-b from-transparent via-[#d4af37] to-transparent" />
        </div>

        <FighterColumn
          name={f2Name}
          photo={f2Photo}
          debut={f2Debut}
          data={f2Data}
          reports={specialistReports}
          color={F2_COLOR}
          debutTextColor="#1a1a1a"
        />
      </div>
    </div>
  );
}
