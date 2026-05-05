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

export interface FighterIntangibles {
  camp?: string | null;
  nationality?: string | null;
  fights_out_of?: string | null;
  weight_miss_history?: string | null;
  short_notice?: boolean | null;
  notice_days?: number | null;
  head_coach?: string | null;
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
  intangibles?: FighterIntangibles;
}

export interface DomainAdvantage {
  f1_offense: number | null;
  f2_defense: number | null;
  f2_offense: number | null;
  f1_defense: number | null;
  f1_pressure: number | null;
  f2_pressure: number | null;
  advantage: number | null; // >0 favors f1, <0 favors f2
}

export interface DomainAdvantages {
  striking?: DomainAdvantage;
  wrestling?: DomainAdvantage;
  takedowns?: DomainAdvantage;
  grappling?: DomainAdvantage;
  submissions?: DomainAdvantage;
}

export interface BetsObject {
  moneyline?: {
    pick?: string;
    win_prob?: number;
    confidence?: "high" | "medium" | "low";
    key_thesis?: string;
  };
  method?: {
    ko_tko?: number;
    submission?: number;
    decision?: number;
  };
  distance?: {
    goes_to_decision?: number;
    ends_inside_distance?: number;
  };
  rounds?: {
    ends_round_1?: number;
    ends_round_2?: number;
    ends_round_3?: number;
    ends_round_4_or_later?: number;
  };
  supporting_specialists?: string[];
  domain_summary?: Record<string, string>;
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
  // New fields from the agent-based pipeline. Optional so older cached
  // analyses (pre-2026-05-05) still render.
  bets?: BetsObject;
  domain_advantages?: DomainAdvantages;
  aggregator_model?: string;
  specialist_reports?: Record<
    string,
    Record<
      string,
      {
        report?: {
          rating_1_to_10?: number;
          [key: string]: unknown;
        };
        narrative?: string;
        [key: string]: unknown;
      }
    >
  >;
  raw_analysis?: string;
  total_stake: number;
  generated_at: string;
}
