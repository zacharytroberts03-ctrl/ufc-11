"use client";

import { useEffect, useState } from "react";
import { fetchCard } from "@/lib/api";
import type { CardData } from "@/lib/types";
import EventBanner from "@/components/EventBanner";
import FightTile from "@/components/FightTile";
import LoadingSpinner from "@/components/LoadingSpinner";

function SectionHeader({ title }: { title: string }) {
  return (
    <div className="flex items-center my-6 -mx-4 sm:-mx-6">
      <div className="flex-1 h-px bg-ufc-border" />
      <div className="bg-ufc-red px-6 py-2">
        <h2 className="text-xs font-black uppercase tracking-[0.35em] text-white">
          {title}
        </h2>
      </div>
      <div className="flex-1 h-px bg-ufc-border" />
    </div>
  );
}

export default function HomePage() {
  const [card, setCard] = useState<CardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCard()
      .then(setCard)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner message="Loading fight card..." />;

  if (error) {
    return (
      <div className="text-center py-20">
        <div className="text-ufc-red text-4xl mb-4">⚠</div>
        <h2 className="text-ufc-text font-bold text-lg mb-2">Backend Offline</h2>
        <p className="text-ufc-muted text-sm mb-6">
          Make sure the FastAPI backend is running:
        </p>
        <code className="bg-ufc-surface border border-ufc-border rounded-lg px-4 py-3 text-ufc-gold text-sm block max-w-md mx-auto">
          cd &quot;AI Websites/UFC 11/backend&quot;<br />
          uvicorn main:app --reload
        </code>
      </div>
    );
  }

  if (!card) return null;

  const mainFights = card.main_card ?? [];
  const prelims = card.prelims ?? [];

  return (
    <div className="animate-fade-in">
      <EventBanner
        eventName={card.event_name || "Upcoming UFC Event"}
        date={card.date || ""}
        location={card.location || ""}
      />

      {/* Main Card */}
      {mainFights.length > 0 && (
        <>
          <SectionHeader title="Main Card" />
          <div className="flex flex-col">
            {mainFights.map((fight, i) => (
              <FightTile key={i} fight={fight} isMainEvent={i === 0} />
            ))}
          </div>
        </>
      )}

      {/* Prelims */}
      {prelims.length > 0 && (
        <>
          <SectionHeader title="Preliminary Card" />
          <div className="flex flex-col">
            {prelims.map((fight, i) => (
              <FightTile key={i} fight={fight} />
            ))}
          </div>
        </>
      )}

      {mainFights.length === 0 && prelims.length === 0 && (
        <div className="text-center py-20 text-ufc-muted">
          No fights found for the current event.
        </div>
      )}
    </div>
  );
}
