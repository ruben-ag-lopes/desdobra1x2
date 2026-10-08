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
  /** Competition name from the official contest (e.g. "Liga das Nações"): picks the model. */
  competition: string;
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

export interface ResumoResponse {
  disponivel: boolean;
  resumo: string | null;
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

/** User-scaled criteria of the trained models: 1 = default, 0 = ignored, 2 = doubled. Missing = 1. */
export type Multipliers = Partial<Record<CriterionId, number>>;

/** Fallback ("criterios-v0") criteria: shares of 100%, unlike the multipliers above. */
export type LegacyCriterionId = "forma" | "ranking_uefa" | "ultimos2" | "confronto_direto" | "classificacao";

/** Direct share per legacy criterion (0-1). Missing = the model's own default. */
export type LegacyWeights = Partial<Record<LegacyCriterionId, number>>;

/** Whole-number percentages per criterion that always add up to 100 (what the user edits). */
export type Shares = Partial<Record<CriterionId, number>>;

/** Every user-editable criterion sent in a desdobramento request. */
export interface Criteria {
  multiplicadores: Multipliers;
  pesosAntigos: LegacyWeights;
  /** The shares the user typed, kept only to show them again; the server only sees `multiplicadores`. */
  partilhas: Shares;
}

export interface Criterion {
  nome: string;
  /** Set when the user can scale this criterion: a CriterionId or a LegacyCriterionId. */
  id: string | null;
  peso: number | null;
  detalhe: string;
}

export interface ModelCriteria {
  modelo: string;
  titulo: string;
  descricao: string;
  criterios: Criterion[];
  /** Weight of every criterion in the model that uses all five (what customising works on). */
  pesos_completos: Record<string, number>;
  dados: string;
  notas: string[];
}

export interface GoalMarket {
  probabilidade: number;
  /** "media_liga": the model did not beat the league's historical frequency, so that is shown instead. */
  fonte: "modelo" | "media_liga";
}

export interface FootballGame {
  id: string;
  competicao: string;
  competicao_nome: string;
  data: string;
  casa: string;
  fora: string;
  /** 1, X, 2; null when the teams have too few games in the league. */
  prob: number[] | null;
  modelo: string | null;
  golos_esperados: number[] | null;
  mais_1_5: number | null; // informational only, not backtested
  mais_2_5: GoalMarket | null;
  mais_3_5: number | null; // informational only, not backtested
  ambas_marcam: GoalMarket | null;
  resultados_provaveis: { casa: number; fora: number; probabilidade: number }[];
  casas_de_apostas: number[] | null;
  casas_mais_2_5: number | null;
}

export interface Competition {
  codigo: string;
  nome: string;
  jogos: number;
}

export interface PrizeTier {
  nome: string;
  vencedores_portugal: number | null;
  vencedores_total: number;
  valor: string;
}

export interface UltimoSorteio {
  game: string;
  concurso: string;
  data_sorteio: string;
  chave: number[];
  chave_extra: number[];
  ordem_saida: number[];
  premios: PrizeTier[];
}

export interface TotobolaResultado {
  numero: string;
  jogo: string;
  resultado: "1" | "X" | "2";
}

export interface UltimoConcursoTotobola {
  game: string;
  concurso: string;
  data_concurso: string;
  resultados: TotobolaResultado[];
  premios: PrizeTier[];
}

export interface NumberFrequency {
  numero: number;
  saidas: number;
  percentagem: number;
  ultimo_sorteio: string | null; // null: didn't come out in the counted window
  data_ultimo_sorteio: string | null;
  ausencias: number;
}

export interface FrequenciaResponse {
  game: string;
  desde: string;
  n_sorteios: number;
  numeros: NumberFrequency[];
}
