import { resolvePhotoUrl } from "@/lib/photoUrl";
import FighterDecagon from "./FighterDecagon";
import type { AnalysisResult } from "@/lib/types";

const F1_COLOR = "#dc0000";  // UFC red
const F2_COLOR = "#d4af37";  // UFC gold

interface Props {
  f1Name: string;
  f2Name: string;
  f1Img?: string | null;
  f2Img?: string | null;
  f1Debut?: boolean;
  f2Debut?: boolean;
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
          className="w-24 h-24 sm:w-32 sm:h-32 rounded-full object-cover shadow-lg"
          style={{ border: `3px solid ${borderColor}` }}
          onError={(e) => {
            const el = e.target as HTMLImageElement;
            el.style.display = "none";
            el.nextElementSibling?.removeAttribute("style");
          }}
        />
      )}
      <div
        className="w-24 h-24 sm:w-32 sm:h-32 rounded-full flex items-center justify-center text-3xl sm:text-4xl font-black"
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

export default function FighterVsHeader({
  f1Name,
  f2Name,
  f1Img,
  f2Img,
  f1Debut,
  f2Debut,
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
        {/* F1 side: photo + name on left, decagon on right */}
        <div className="flex flex-col sm:flex-row items-center gap-4">
          <div className="flex flex-col items-center gap-2 sm:items-start">
            <FighterPhoto name={f1Name} img={f1Photo} borderColor={F1_COLOR} />
            {f1Debut && (
              <span className="text-[10px] font-black tracking-widest uppercase px-2 py-0.5 rounded"
                    style={{ backgroundColor: F1_COLOR, color: "#fff" }}>
                UFC DEBUT
              </span>
            )}
            <h2 className="text-lg sm:text-xl font-black text-white text-center sm:text-left leading-tight max-w-[10rem]">
              {f1Name}
            </h2>
          </div>
          <div className="flex-shrink-0">
            <FighterDecagon
              reports={specialistReports}
              fighterName={f1Name}
              color={F1_COLOR}
              size={200}
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

        {/* F2 side: decagon on left, photo + name on right (mirrored) */}
        <div className="flex flex-col-reverse sm:flex-row items-center gap-4 md:justify-end">
          <div className="flex-shrink-0">
            <FighterDecagon
              reports={specialistReports}
              fighterName={f2Name}
              color={F2_COLOR}
              size={200}
            />
          </div>
          <div className="flex flex-col items-center gap-2 sm:items-end">
            <FighterPhoto name={f2Name} img={f2Photo} borderColor={F2_COLOR} />
            {f2Debut && (
              <span className="text-[10px] font-black tracking-widest uppercase px-2 py-0.5 rounded"
                    style={{ backgroundColor: F2_COLOR, color: "#1a1a1a" }}>
                UFC DEBUT
              </span>
            )}
            <h2 className="text-lg sm:text-xl font-black text-white text-center sm:text-right leading-tight max-w-[10rem]">
              {f2Name}
            </h2>
          </div>
        </div>
      </div>
    </div>
  );
}
