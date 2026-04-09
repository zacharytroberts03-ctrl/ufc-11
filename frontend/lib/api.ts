import type { CardData, OddsData, AnalysisResult, FighterData } from "./types";

const BASE = "http://localhost:8000";

export async function fetchCard(): Promise<CardData> {
  const res = await fetch(`${BASE}/api/card`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch card: ${res.status}`);
  return res.json();
}

export async function fetchOdds(f1: string, f2: string): Promise<OddsData> {
  const res = await fetch(
    `${BASE}/api/odds/${encodeURIComponent(f1)}/${encodeURIComponent(f2)}`,
    { cache: "no-store" }
  );
  if (!res.ok) return { available: false };
  return res.json();
}

export async function fetchCachedAnalysis(
  f1: string,
  f2: string
): Promise<AnalysisResult | null> {
  try {
    const res = await fetch(
      `${BASE}/api/analysis/lookup/${encodeURIComponent(f1)}/${encodeURIComponent(f2)}`,
      { cache: "no-store" }
    );
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchFighter(name: string): Promise<FighterData | null> {
  try {
    const res = await fetch(
      `${BASE}/api/fighter/${encodeURIComponent(name)}`,
      { cache: "no-store" }
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function runAnalysis(
  f1: string,
  f2: string,
  totalStake: number = 100,
  eventContext: Record<string, unknown> = {}
): Promise<AnalysisResult> {
  const res = await fetch(`${BASE}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      f1,
      f2,
      total_stake: totalStake,
      event_context: eventContext,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed: ${res.status}`);
  }
  return res.json();
}
