"""Upcoming games of the covered leagues, searchable, with 1X2 and goal forecasts."""

from datetime import datetime, timedelta

from app.cache import TTLCache
from app.models import Competition, ExactScore, FootballGame, GoalMarket
from app.research import data
from app.services import trained_model
from app.services.trained_model import plain_name

_cache = TTLCache(ttl_seconds=3600)
MAX_GAMES = 80
_QUERY_STOPWORDS = {"fc", "sc", "cf", "sl", "cd", "ac", "as", "afc", "vs", "x", "-"}


def _fixtures() -> list[data.Fixture]:
    recent = datetime.now() - timedelta(hours=2)  # keep games that have just started
    return [
        f
        for f in _cache.get_or_set("fixtures", data.load_fixtures)
        if f.league in trained_model.BY_CODE and f.kickoff >= recent
    ]


def _game_id(f: data.Fixture) -> str:
    return "-".join([f.league, f"{f.kickoff:%Y%m%d}", plain_name(f.home).replace(" ", "_"), plain_name(f.away).replace(" ", "_")])


def _search_names(league: str, team: str) -> str:
    """The team's dataset name plus the Portuguese/full names that point to it (e.g. "sporting" -> "Sp Lisbon")."""
    aliases = trained_model.BY_CODE[league].aliases
    return " ".join([plain_name(team), *(alias for alias, target in aliases.items() if target == team)])


def _matches_query(f: data.Fixture, query: str) -> bool:
    words = [w for w in plain_name(query).split() if w not in _QUERY_STOPWORDS]
    text = " ".join(
        [_search_names(f.league, f.home), _search_names(f.league, f.away), plain_name(trained_model.BY_CODE[f.league].title)]
    )
    return all(w in text for w in words)


def _no_margin(odds: tuple[float, ...] | None) -> list[float] | None:
    if not odds:
        return None
    implied = [1 / o for o in odds]
    return [p / sum(implied) for p in implied]


def competitions() -> list[Competition]:
    counts: dict[str, int] = {}
    for f in _fixtures():
        counts[f.league] = counts.get(f.league, 0) + 1
    return [
        Competition(codigo=spec.code, nome=spec.title, jogos=counts.get(spec.code, 0))
        for spec in trained_model.LEAGUES
    ]


def games(
    competicao: str | None = None,
    q: str | None = None,
    dias: int | None = None,
    multiplicadores: dict[str, float] | None = None,
) -> list[FootballGame]:
    selected = _fixtures()
    if competicao:
        selected = [f for f in selected if f.league == competicao]
    if q:
        selected = [f for f in selected if _matches_query(f, q)]
    if dias:
        until = datetime.now() + timedelta(days=dias)
        selected = [f for f in selected if f.kickoff <= until]
    selected = selected[:MAX_GAMES]

    forecasts: dict[int, trained_model.Forecast | None] = {}
    for league in dict.fromkeys(f.league for f in selected):
        idx = [i for i, f in enumerate(selected) if f.league == league]
        try:
            results = trained_model.forecast_league(
                league, [(selected[i].home, selected[i].away) for i in idx], multiplicadores
            )
        except Exception:
            results = [None] * len(idx)  # league data unavailable: list the games without a forecast
        forecasts.update(zip(idx, results))

    out = []
    for i, f in enumerate(selected):
        game = FootballGame(
            id=_game_id(f),
            competicao=f.league,
            competicao_nome=trained_model.BY_CODE[f.league].title,
            data=f.kickoff,
            casa=f.home,
            fora=f.away,
            casas_de_apostas=_no_margin(f.odds),
            casas_mais_2_5=(_no_margin(f.ou25_odds) or [None])[0],
        )
        fc = forecasts.get(i)
        if fc:
            over, over_from_model = fc.goal_markets["over25"]
            btts, btts_from_model = fc.goal_markets["btts"]
            game.prob = list(fc.probs)
            game.modelo = fc.version
            game.golos_esperados = list(fc.expected_goals)
            game.mais_1_5 = fc.other_goal_lines["over15"]
            game.mais_2_5 = GoalMarket(probabilidade=over, fonte="modelo" if over_from_model else "media_liga")
            game.mais_3_5 = fc.other_goal_lines["over35"]
            game.ambas_marcam = GoalMarket(probabilidade=btts, fonte="modelo" if btts_from_model else "media_liga")
            game.resultados_provaveis = [ExactScore(casa=h, fora=a, probabilidade=p) for h, a, p in fc.top_scores]
        out.append(game)
    return out
