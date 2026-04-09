"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";

interface Props {
  title: string;
  content: string;
  icon?: string;
  defaultOpen?: boolean;
  accentColor?: "red" | "gold" | "green";
}

export default function AnalysisSection({
  title,
  content,
  icon = "🥊",
  defaultOpen = false,
  accentColor = "red",
}: Props) {
  const [open, setOpen] = useState(defaultOpen);

  const accentClass = {
    red: "border-ufc-red/40 bg-ufc-red/5",
    gold: "border-ufc-gold/40 bg-ufc-gold/5",
    green: "border-ufc-green/40 bg-ufc-green/5",
  }[accentColor];

  const headerAccent = {
    red: "text-ufc-red",
    gold: "text-ufc-gold",
    green: "text-ufc-green",
  }[accentColor];

  const leftBorder = {
    red: "border-l-ufc-red",
    gold: "border-l-ufc-gold",
    green: "border-l-ufc-green",
  }[accentColor];

  return (
    <div className={`rounded-xl border ${accentClass} overflow-hidden mb-4 animate-slide-up`}>
      <button
        onClick={() => setOpen(!open)}
        className={`w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/5 transition-colors`}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{icon}</span>
          <span className={`font-bold text-sm uppercase tracking-wider ${headerAccent}`}>
            {title}
          </span>
        </div>
        <svg
          className={`w-4 h-4 text-ufc-muted transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className={`px-5 pb-5 border-t border-ufc-border/50 border-l-4 ${leftBorder}`}>
          <div className="markdown-content pt-4">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
