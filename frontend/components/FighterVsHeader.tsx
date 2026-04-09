interface Props {
  f1Name: string;
  f2Name: string;
  f1Img?: string | null;
  f2Img?: string | null;
  f1Debut?: boolean;
  f2Debut?: boolean;
}

function FighterSlot({
  name,
  img,
  isDebut,
  align,
}: {
  name: string;
  img?: string | null;
  isDebut?: boolean;
  align: "left" | "right";
}) {
  const imgSrc = img?.startsWith("/fighter_photos")
    ? `http://localhost:8000${img}`
    : img;

  return (
    <div className={`flex flex-col items-center gap-3 ${align === "right" ? "items-end" : "items-start"} sm:items-center`}>
      {/* Photo */}
      <div className="relative">
        {imgSrc ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={imgSrc}
            alt={name}
            className="w-28 h-28 sm:w-36 sm:h-36 rounded-full object-cover border-2 border-ufc-red shadow-xl"
            onError={(e) => {
              const el = e.target as HTMLImageElement;
              el.style.display = "none";
              el.nextElementSibling?.removeAttribute("style");
            }}
          />
        ) : null}
        <div
          className="w-28 h-28 sm:w-36 sm:h-36 rounded-full bg-ufc-elevated border-2 border-ufc-red flex items-center justify-center text-4xl font-black text-ufc-red"
          style={imgSrc ? { display: "none" } : {}}
        >
          {name[0]}
        </div>
      </div>

      {/* Name */}
      <div className="text-center">
        {isDebut && (
          <span className="block text-[10px] font-black tracking-widest uppercase text-ufc-red mb-1">
            UFC Debut
          </span>
        )}
        <h2 className="text-lg sm:text-xl font-black text-ufc-text leading-tight text-center">
          {name}
        </h2>
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
}: Props) {
  return (
    <div className="card p-6 sm:p-8 mb-6 border-2 border-ufc-red">
      <div className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center">
        <FighterSlot
          name={f1Name}
          img={f1Img}
          isDebut={f1Debut}
          align="left"
        />

        <div className="flex flex-col items-center gap-1 px-2">
          <span className="text-ufc-red text-2xl sm:text-3xl font-black tracking-widest">
            VS
          </span>
        </div>

        <FighterSlot
          name={f2Name}
          img={f2Img}
          isDebut={f2Debut}
          align="right"
        />
      </div>
    </div>
  );
}
