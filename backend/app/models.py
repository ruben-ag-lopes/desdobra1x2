from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Draw(BaseModel):
    """A single upcoming/active draw or matchday for a game."""

    game: Literal["totobola", "totobola_extra", "totoloto", "euromilhoes", "eurodreams"]
    concurso: str
    contest_id: str | None = None
    fecha_apostas: datetime | None = None
    data_sorteio: date | None = None


class FixtureInfo(BaseModel):
    """A fixture listed in an official Totobola contest."""

    home_team: str
    away_team: str
    competition: str = ""


class ManualTeamStats(BaseModel):
    """Fallback stats the user fills in when the team isn't covered by the free API."""

    recent_form: list[Literal["W", "D", "L"]] = []  # last 5 games this season
    last2_in_competition: list[Literal["W", "D", "L"]] = []
    domestic_position: int | None = None
    domestic_total_teams: int | None = None


class MatchInput(BaseModel):
    id: str
    home_team: str
    away_team: str
    home_country: str
    away_country: str
    competition_code: str | None = None  # football-data.org code, e.g. "PPL"; None => manual only
    competition: str = ""  # name shown by Santa Casa, e.g. "Liga das Nações": picks the model to use
    home_is_loaned_venue: bool | None = None  # override auto-detection when set
    manual_home_stats: ManualTeamStats | None = None
    manual_away_stats: ManualTeamStats | None = None
    manual_h2h: list[Literal["1", "X", "2"]] = []  # last up-to-5 years, from home team's perspective
    # User's choice: 1 outcome = fixed in every bet (not predicted); 2 outcomes = "dupla", the model's
    # probabilities are renormalized over those two and the bets only use them; empty = free.
    fixed_results: list[Literal["1", "X", "2"]] = Field(default=[], max_length=2)

    @field_validator("fixed_results")
    @classmethod
    def _distinct(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("fixed_results must not repeat an outcome")
        return value


class ResultProbabilities(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    prob_home: float
    prob_draw: float
    prob_away: float
    criteria_breakdown: dict[str, dict[str, float | str]]
    fixed_results: list[Literal["1", "X", "2"]] = []
    probs_modelo: list[float] | None = None  # model's 1/X/2 before applying a "dupla"
    modelo: str = ""  # which model produced the probabilities (or "fixo")
    low_confidence: bool = False  # no historical data for these teams: rough heuristic only
    # Goal markets (only if model supports them and backtest shows they beat league frequency).
    prob_over25: float | None = None  # P(3+ goals)
    prob_btts: float | None = None  # P(both teams score)
    goal_modelo: str = ""  # which model produced goal market predictions, if any


MAX_APOSTAS = 500
MAX_MATCHES = 20


# Criteria the user can scale (same ids as app.research.importance.CRITERIA).
CriterionId = Literal["elo", "casa", "ataque", "defesa", "h2h"]
Multiplier = Annotated[float, Field(ge=0, le=2)]

# Fallback ("criterios-v0") criteria: a pie of shares (same ids as
# app.services.totobola_engine.LEGACY_WEIGHTS_DEFAULT). Each is at most 100% and, unlike the
# multiplicadores above, they must not together add up to more than 100%.
LegacyCriterionId = Literal["forma", "ranking_uefa", "ultimos2", "confronto_direto", "classificacao"]
Share = Annotated[float, Field(ge=0, le=1)]


class DesdobramentoRequest(BaseModel):
    matches: list[MatchInput] = Field(max_length=MAX_MATCHES)
    n_apostas: int = Field(ge=1, le=MAX_APOSTAS)
    concurso: str | None = None  # stored with the predictions (BigQuery), optional
    data_sorteio: date | None = None
    # User-scaled criteria of the trained models: 1 = default, 0 = ignore it, 2 = double it. Empty = defaults.
    multiplicadores: dict[CriterionId, Multiplier] = {}
    # Fallback-model criteria (used only for matches with no trained model): direct shares, empty = defaults.
    pesos_antigos: dict[LegacyCriterionId, Share] = {}
    bonus_casa: Share | None = None  # home-side bonus of the fallback model; None = default (10%)

    @model_validator(mode="after")
    def _pesos_antigos_nao_ultrapassam_100(self) -> "DesdobramentoRequest":
        total = sum(self.pesos_antigos.values())
        if total > 1.0 + 1e-9:
            raise ValueError(f"pesos_antigos somam {total:.0%}, mais do que 100%")
        return self


class DesdobramentoResponse(BaseModel):
    probabilities: list[ResultProbabilities]
    apostas: list[list[Literal["1", "X", "2"]]]


class ResumoRequest(BaseModel):
    """The already-computed result of a /desdobramento call: the AI only explains these numbers."""

    probabilities: list[ResultProbabilities] = Field(max_length=MAX_MATCHES)
    n_apostas: int = Field(ge=1, le=MAX_APOSTAS)


class ResumoResponse(BaseModel):
    disponivel: bool  # False when no AI provider is configured (ANTHROPIC_API_KEY unset)
    resumo: str | None = None


class PrizeTier(BaseModel):
    nome: str
    vencedores_portugal: int | None = None  # None when the game doesn't split Portugal vs. total (e.g. Totoloto)
    vencedores_total: int
    valor: str  # free text: "€ 130.000.000,00" or "20.000/mês x 30 anos" (annuity jackpots)


class UltimoSorteio(BaseModel):
    """Winning key and prize table of a game's most recent draw (docs/plano-numeros-frequentes.md)."""

    game: str
    concurso: str
    data_sorteio: date
    chave: list[int]
    chave_extra: list[int] = []  # stars, dream number, lucky number...
    ordem_saida: list[int]
    premios: list[PrizeTier]


class NumberFrequency(BaseModel):
    numero: int
    saidas: int
    percentagem: float
    ultimo_sorteio: str
    data_ultimo_sorteio: date
    ausencias: int  # draws since this number last came out


class FrequenciaResponse(BaseModel):
    game: str
    desde: date  # data has been tracked since this date (not a rolling window — see the scraper's docstring)
    numeros: list[NumberFrequency]


class LotteryTicket(BaseModel):
    numbers: list[int]
    extra_numbers: list[int] = []


class LotteryGenerateRequest(BaseModel):
    count: int = 1


class LotteryGenerateResponse(BaseModel):
    tickets: list[LotteryTicket]


class Criterion(BaseModel):
    nome: str
    # Set when the user can scale this criterion: a `multiplicadores` id (trained models) or a
    # `pesos_antigos` id (fallback model) — see CriterionId and LegacyCriterionId above.
    id: str | None = None
    peso: float | None = None  # share of influence in [0, 1]; None when not quantifiable
    detalhe: str = ""


class ModelCriteria(BaseModel):
    """Plain-language description of a prediction model, for the criteria pop-up."""

    modelo: str
    titulo: str
    descricao: str
    criterios: list[Criterion]
    dados: str = ""
    notas: list[str] = []


class GoalMarket(BaseModel):
    probabilidade: float
    fonte: Literal["modelo", "media_liga"]  # the model only where it beat the league's frequency in the backtest


class ExactScore(BaseModel):
    casa: int
    fora: int
    probabilidade: float


class FootballGame(BaseModel):
    """An upcoming game of a covered league, with our forecast and the bookmakers' reference."""

    id: str
    competicao: str  # football-data.co.uk code, e.g. "E0"
    competicao_nome: str
    data: datetime
    casa: str
    fora: str
    prob: list[float] | None = None  # 1, X, 2; None when the teams have too few games in the league
    modelo: str | None = None
    golos_esperados: list[float] | None = None  # home, away
    mais_1_5: float | None = None  # informational only, not backtested (see other_goal_lines)
    mais_2_5: GoalMarket | None = None
    mais_3_5: float | None = None  # informational only, not backtested
    ambas_marcam: GoalMarket | None = None
    resultados_provaveis: list[ExactScore] = []
    casas_de_apostas: list[float] | None = None  # 1, X, 2 implied by the average odds, margin removed
    casas_mais_2_5: float | None = None


class Competition(BaseModel):
    codigo: str
    nome: str
    jogos: int  # upcoming games listed
