"use client";

import { useRouter } from "next/navigation";
import type { Fight } from "@/lib/types";

interface Props {
  fight: Fight;
  isMainEvent?: boolean;
}

function FighterPhoto({
  img,
  name,
  isMainEvent,
}: {
  img?: string | null;
  name: string;
  isMainEvent?: boolean;
}) {
  const src = img?.startsWith("/fighter_photos")
    ? `http://localhost:8000${img}`
    : img;

  const sizeClass = isMainEvent ? "w-14 h-14" : "w-12 h-12";
  const borderClass = isMainEvent
    ? "border-2 border-ufc-red"
    : "border border-ufc-border group-hover:border-ufc-red/50";

  if (src) {
    return (
      /* eslint-disable-next-line @next/next/no-img-element */
      <img
        src={src}
        alt={name}
        className={`${sizeClass} ${borderClass} rounded-full object-cover flex-shrink-0 transition-colors`}
        onError={(e) => {
          const el = e.target as HTMLImageElement;
          el.style.display = "none";
          (el.nextElementSibling as HTMLElement | null)?.removeAttribute("style");
        }}
      />
    );
  }

  return (
    <div
      className={`${sizeClass} ${borderClass} rounded-full flex items-center justify-center font-black text-ufc-red flex-shrink-0 bg-ufc-elevated transition-colors`}
    >
      {name[0]}
    </div>
  );
}

export default function FightTile({ fight, isMainEvent }: Props) {
  const router = useRouter();

  const handleClick = () => {
    const f1 = encodeURIComponent(fight.fighter1);
    const f2 = encodeURIComponent(fight.fighter2);
    router.push(`/fight/${f1}/${f2}`);
  };

  return (
    <button
      onClick={handleClick}
      className={`
        group w-full text-left relative overflow-hidden
        border-b transition-all duration-200 cursor-pointer
        ${isMainEvent
          ? "border-b-ufc-red/40 bg-white hover:bg-ufc-elevated"
          : "border-b-ufc-border bg-white hover:bg-ufc-elevated"
        }
      `}
    >
      {/* Main event: red left accent bar */}
      {isMainEvent && (
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-ufc-red" />
      )}

      <div className={`flex items-center ${isMainEvent ? "px-5 sm:px-7 py-5" : "px-4 sm:px-6 py-3.5"}`}>

        {/* Fighter 1 — left */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <FighterPhoto img={fight.f1_img} name={fight.fighter1} isMainEvent={isMainEvent} />
          <div className="min-w-0">
            {isMainEvent && (
              <span className="block text-[9px] font-black tracking-widest uppercase text-ufc-red mb-0.5">
                Main Event
              </span>
            )}
            <span
              className={`font-black leading-tight block truncate text-black
                ${isMainEvent ? "text-base" : "text-sm"}
              `}
            >
              {fight.fighter1}
            </span>
          </div>
        </div>

        {/* Center: VS + weight class */}
        <div className="flex flex-col items-center gap-1 px-3 sm:px-6 flex-shrink-0">
          <span
            className={`font-black tracking-widest text-ufc-red ${isMainEvent ? "text-lg" : "text-sm"}`}
          >
            VS
          </span>
          {fight.weight_class && fight.weight_class !== "N/A" && (
            <span className="text-[9px] font-bold uppercase tracking-wider text-ufc-muted whitespace-nowrap">
              {fight.weight_class}
            </span>
          )}
        </div>

        {/* Fighter 2 — right (mirrored) */}
        <div className="flex items-center gap-3 flex-1 min-w-0 flex-row-reverse">
          <FighterPhoto img={fight.f2_img} name={fight.fighter2} isMainEvent={isMainEvent} />
          <div className="min-w-0 text-right">
            <span
              className={`font-black leading-tight block truncate text-black
                ${isMainEvent ? "text-base" : "text-sm"}
              `}
            >
              {fight.fighter2}
            </span>
          </div>
        </div>

        {/* Chevron */}
        <svg
          className="w-4 h-4 text-ufc-border group-hover:text-ufc-red transition-colors ml-3 flex-shrink-0 group-hover:translate-x-0.5 transition-transform"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  );
}
