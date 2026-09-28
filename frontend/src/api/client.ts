import type {
  Competition,
  Criteria,
  DesdobramentoResponse,
  Draw,
  FixtureInfo,
  FootballGame,
  LotteryTicket,
  MatchInput,
  ModelCriteria,
  Multipliers,
} from "./types";

// Backend URL. Default: localhost in development, same domain in production (Vercel Services
// routes /api to the backend). Set VITE_API_URL when the API lives elsewhere (e.g. Render).
const BASE_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "http://localhost:8000" : "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`${resp.status}: ${body}`);
  }
  return resp.json();
}

export function getTotobolaDraws(): Promise<Draw[]> {
  return request("/api/totobola/draws");
}

export function getContestMatches(contestId: string): Promise<FixtureInfo[]> {
  return request(`/api/totobola/draws/${contestId}/matches`);
}

export function getCriterios(modelos: string[]): Promise<ModelCriteria[]> {
  return request(`/api/totobola/criterios?modelos=${encodeURIComponent(modelos.join(","))}`);
}

export function postDesdobramento(
  matches: MatchInput[],
  n_apostas: number,
  draw?: { concurso: string; data_sorteio: string | null },
  criteria: Criteria = { multiplicadores: {}, pesosAntigos: {} },
): Promise<DesdobramentoResponse> {
  return request("/api/totobola/desdobramento", {
    method: "POST",
    body: JSON.stringify({
      matches,
      n_apostas,
      concurso: draw?.concurso,
      data_sorteio: draw?.data_sorteio,
      multiplicadores: criteria.multiplicadores,
      pesos_antigos: criteria.pesosAntigos,
    }),
  });
}

export function getLotteryDraw(game: "totoloto" | "euromilhoes" | "eurodreams"): Promise<Draw | null> {
  return request(`/api/lotteries/${game}/draw`);
}

export function generateLotteryTickets(
  game: "totoloto" | "euromilhoes" | "eurodreams",
  count: number,
): Promise<{ tickets: LotteryTicket[] }> {
  return request(`/api/lotteries/${game}/generate`, {
    method: "POST",
    body: JSON.stringify({ count }),
  });
}

export function getCompeticoes(): Promise<Competition[]> {
  return request("/api/futebol/competicoes");
}

export function getJogos(
  filters: { competicao?: string; q?: string; dias?: number },
  multiplicadores: Multipliers = {},
): Promise<FootballGame[]> {
  const params = new URLSearchParams();
  if (filters.competicao) params.set("competicao", filters.competicao);
  if (filters.q) params.set("q", filters.q);
  if (filters.dias) params.set("dias", String(filters.dias));
  if (Object.keys(multiplicadores).length > 0) params.set("criterios", JSON.stringify(multiplicadores));
  return request(`/api/futebol/jogos?${params}`);
}
