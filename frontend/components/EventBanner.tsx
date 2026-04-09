interface Props {
  eventName: string;
  date: string;
  location: string;
}

export default function EventBanner({ eventName, date, location }: Props) {
  return (
    <div className="relative overflow-hidden rounded-2xl mb-10 bg-hero-gradient border-2 border-ufc-red">
      {/* Red accent line */}
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-ufc-red" />

      {/* Background pattern */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage:
            "repeating-linear-gradient(45deg, #dc0000 0, #dc0000 1px, transparent 0, transparent 50%)",
          backgroundSize: "20px 20px",
        }}
      />

      <div className="relative px-8 py-8 sm:py-10">
        <div className="flex items-center gap-2 mb-3">
          <span className="bg-ufc-red text-white text-xs font-black px-2.5 py-1 rounded tracking-widest uppercase">
            UFC
          </span>
          <span className="text-ufc-muted text-xs tracking-widest uppercase font-semibold">
            Fight Night
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-ufc-red tracking-tight leading-none mb-4">
          {eventName}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-sm">
          <span className="flex items-center gap-1.5 text-ufc-gold font-semibold">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {date}
          </span>
          <span className="flex items-center gap-1.5 text-ufc-muted">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {location}
          </span>
        </div>
      </div>
    </div>
  );
}
