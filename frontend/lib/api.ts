import type { CardData, OddsData, AnalysisResult, FighterData } from "./types";

// Data is published as static JSON by the daily refresh_cache.py cron, which
// commits the files and lets Vercel auto-redeploy. There is no live backend.
const CARD_URL = "/data/card.json";
const ANALYSES_URL = "/data/analyses.json";

interface AnalysesFile {
  event_key: string | null;
  generated_at: string | null;
  fights: Record<string, AnalysisResult>;
}

let _analysesPromise: Promise<AnalysesFile> | null = null;

function loadAnalyses(): Promise<AnalysesFile> {
  if (!_analysesPromise) {
    _analysesPromise = fetch(ANALYSES_URL, { cache: "no-store" }).then((res) => {
      if (!res.ok) throw new Error(`Failed to load analyses: ${res.status}`);
      return res.json();
    });
  }
  return _analysesPromise;
}

function slug(s: string): string {
  return (
    s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "unknown"
  );
}

function fightKey(f1: string, f2: string): string {
  const [a, b] = [slug(f1), slug(f2)].sort();
  return `${a}__${b}`;
}

export async function fetchCard(): Promise<CardData> {
  const res = await fetch(CARD_URL, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch card: ${res.status}`);
  return res.json();
}

export async function fetchOdds(f1: string, f2: string): Promise<OddsData> {
  try {
    const data = await loadAnalyses();
    const fight = data.fights[fightKey(f1, f2)];
    const odds = fight?.odds_data;
    if (!odds) return { available: false };
    return {
      available: true,
      fighter1: odds.fighter1 ?? f1,
      fighter2: odds.fighter2 ?? f2,
      books: odds.books,
      best_f1: odds.best_f1,
      best_f2: odds.best_f2,
      hedge: fight?.hedge_summary ?? undefined,
    };
  } catch {
    return { available: false };
  }
}

export async function fetchCachedAnalysis(
  f1: string,
  f2: string
): Promise<AnalysisResult | null> {
  try {
    const data = await loadAnalyses();
    return data.fights[fightKey(f1, f2)] ?? null;
  } catch {
    return null;
  }
}

export async function fetchFighter(name: string): Promise<FighterData | null> {
  // Cached fighter data already lives inside each AnalysisResult.f1_data /
  // f2_data, so this fallback is only used if a caller asks about a fighter
  // not on the current card. On the deployed site we have no live scraper.
  try {
    const data = await loadAnalyses();
    const target = name.toLowerCase();
    for (const fight of Object.values(data.fights)) {
      if (fight.f1_data?.name?.toLowerCase() === target) return fight.f1_data;
      if (fight.f2_data?.name?.toLowerCase() === target) return fight.f2_data;
    }
    return null;
  } catch {
    return null;
  }
}

export async function runAnalysis(
  _f1: string,
  _f2: string,
  _totalStake: number = 100,
  _eventContext: Record<string, unknown> = {}
): Promise<AnalysisResult> {
  throw new Error(
    "Live analysis is not available on the deployed site — analyses are precomputed daily."
  );
}
