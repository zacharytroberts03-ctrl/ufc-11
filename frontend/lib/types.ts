export interface Fight {
  fighter1: string;
  fighter2: string;
  weight_class?: string;
  f1_img?: string | null;
  f2_img?: string | null;
}

export interface CardData {
  event_name: string;
  date: string;
  location: string;
  main_card: Fight[];
  prelims: Fight[];
}

export interface BookOdds {
  name: string;
  f1_odds: number;
  f2_odds: number;
  f1_best: boolean;
  f2_best: boolean;
  f1_name?: string;
  f2_name?: string;
}

export interface HedgeSummary {
  arb_exists: boolean;
  roi_pct: number;
  guaranteed_profit: number;
  f1_name: string;
  f2_name: string;
  f1_stake: number;
  f2_stake: number;
  f1_book: string;
  f2_book: string;
  f1_odds: number;
  f2_odds: number;
  total_stake: number;
  annotated_books: BookOdds[];
}

export interface OddsData {
  available: boolean;
  fighter1?: string;
  fighter2?: string;
  books?: BookOdds[];
  best_f1?: { book: string; odds: number };
  best_f2?: { book: string; odds: number };
  hedge?: HedgeSummary;
  error?: string;
}

export interface FighterRecord {
  wins: string;
  losses: string;
  draws: string;
}

export interface FighterStriking {
  slpm: string;
  sapm: string;
  str_acc: string;
  str_def: string;
}

export interface FighterGrappling {
  td_avg: string;
  td_acc: string;
  td_def: string;
  sub_avg: string;
}

export interface FightHistoryEntry {
  result: string;
  opponent: string;
  method: string;
  round?: string;
  time?: string;
  promotion?: string;
  date?: string;
}

export interface FighterData {
  name: string;
  record: FighterRecord;
  striking: FighterStriking;
  grappling: FighterGrappling;
  win_methods: { ko: string; sub: string; dec: string; note?: string };
  fight_history: FightHistoryEntry[];
  height: string;
  weight: string;
  reach: string;
  stance: string;
  ufc_debut?: boolean;
  debut_source?: string;
  photo_url?: string | null;
  dob?: string;
}

export interface AnalysisResult {
  f1_name: string;
  f2_name: string;
  f1_data: FighterData;
  f2_data: FighterData;
  f1_img?: string | null;
  f2_img?: string | null;
  odds_data?: OddsData | null;
  hedge_summary?: HedgeSummary | null;
  analysis_sections: {
    f1_profile?: string;
    f2_profile?: string;
    head2head?: string;
    endings?: string;
    betting?: string;
  };
  raw_analysis?: string;
  total_stake: number;
  generated_at: string;
}
