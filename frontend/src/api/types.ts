export type Outcome = "1" | "X" | "2";
export type ResultLetter = "W" | "D" | "L";

export interface Draw {
  game: "totobola" | "totobola_extra" | "totoloto" | "euromilhoes" | "eurodreams";
  concurso: string;
  contest_id: string | null;
  fecha_apostas: string | null;
  data_sorteio: string | null;
}

export interface ManualTeamStats {
  recent_form: ResultLetter[];
  last2_in_competition: ResultLetter[];
  domestic_position: number | null;
  domestic_total_teams: number | null;
}

export interface MatchInput {
  id: string;
  home_team: string;
  away_team: string;
  home_country: string;
  away_country: string;
  competition_code: string | null;
  home_is_loaned_venue: boolean | null;
  manual_home_stats: ManualTeamStats | null;
  manual_away_stats: ManualTeamStats | null;
  manual_h2h: Outcome[];
  /** 1 outcome = fixed in every bet; 2 = "dupla" (probabilities renormalized over the pair); empty = free. */
  fixed_results: Outcome[];
}

export interface ResultProbabilities {
  match_id: string;
  home_team: string;
  away_team: string;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  criteria_breakdown: Record<string, Record<string, number | string>>;
  fixed_results: Outcome[];
  probs_modelo: number[] | null;
  modelo: string;
  low_confidence: boolean;
}

export interface DesdobramentoResponse {
  probabilities: ResultProbabilities[];
  apostas: Outcome[][];
}

export interface LotteryTicket {
  numbers: number[];
  extra_numbers: number[];
}

export interface FixtureInfo {
  home_team: string;
  away_team: string;
  competition: string;
}

export type CriterionId = "elo" | "casa" | "ataque" | "defesa" | "h2h";

/** User-scaled criteria: 1 = default, 0 = ignored, 2 = doubled. Missing = 1. */
export type Multipliers = Partial<Record<CriterionId, number>>;

export interface Criterion {
  nome: string;
  /** Set when the user can scale this criterion. */
  id: CriterionId | null;
  peso: number | null;
  detalhe: string;
}

export interface ModelCriteria {
  modelo: string;
  titulo: string;
  descricao: string;
  criterios: Criterion[];
  dados: string;
  notas: string[];
}
