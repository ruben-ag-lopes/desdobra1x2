from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


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


MAX_APOSTAS = 500
MAX_MATCHES = 20


class CriterionInfo(BaseModel):
    """A customizable criterion with its stable ID and default multiplier."""

    id: str  # e.g., "elo", "casa", "ataque", "defesa", "h2h"
    label: str  # display name
    multiplier_default: float = 1.0  # neutral is 1.0; 0 = disable, 2 = double effect


class DesdobramentoRequest(BaseModel):
    matches: list[MatchInput] = Field(max_length=MAX_MATCHES)
    n_apostas: int = Field(ge=1, le=MAX_APOSTAS)
    concurso: str | None = None  # stored with the predictions (BigQuery), optional
    data_sorteio: date | None = None
    # Optional: customize criteria. Keys are criterion IDs, values are multipliers [0, 2].
    # Omitted = use defaults. Not supported for "criterios-v0" and "elo-direto-v1".
    criteria_multipliers: dict[str, float] = Field(default_factory=dict)


class DesdobramentoResponse(BaseModel):
    probabilities: list[ResultProbabilities]
    apostas: list[list[Literal["1", "X", "2"]]]


class LotteryTicket(BaseModel):
    numbers: list[int]
    extra_numbers: list[int] = []


class LotteryGenerateRequest(BaseModel):
    count: int = 1


class LotteryGenerateResponse(BaseModel):
    tickets: list[LotteryTicket]


class Criterion(BaseModel):
    nome: str
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
