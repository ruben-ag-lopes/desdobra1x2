"""Production 1X2 predictions from models fitted on historical results.

One "domain" per team pool (national teams, or one domestic league). Each domain
uses the model that won its walk-forward backtest (`python -m app.research.backtest`,
results in docs/plano-competicoes.md); when two models were within 0.002 log loss,
the simpler Elo model is kept. Domains are trained lazily, only when a fixture
needs them, and refitted at most every 12h on data that includes the latest results.
"""

import difflib
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

import numpy as np

from app.cache import TTLCache
from app.research import data
from app.research.features import MIN_PRIOR_GAMES, FeatureState, Rows, build_rows_and_state, fixture_rows
from app.research.importance import apply_multipliers, criteria_weights, neutral_values
from app.research.models import MAX_GOALS, OrderedLogitElo, PoissonModel
from app.scrapers.elo_ratings import _PT_TO_EN

_cache = TTLCache(ttl_seconds=12 * 3600)

Probs = tuple[float, float, float]


def plain_name(name: str) -> str:
    stripped = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")
    return " ".join(stripped.lower().split())


# eloratings.net-style English names (from _PT_TO_EN) -> martj42 dataset names
_NATIONS_DATASET_ALIASES = {"Czechia": "Czech Republic", "Ireland": "Republic of Ireland"}

# Santa Casa / Portuguese / full club names -> football-data.co.uk names, keyed by plain_name(name).
# Names that already match the dataset (after plain_name) or are within the fuzzy cutoff need no entry.
_CLUB_ALIASES: dict[str, dict[str, str]] = {
    "P1": {
        "sporting": "Sp Lisbon", "sporting cp": "Sp Lisbon", "sporting clube de portugal": "Sp Lisbon",
        "fc porto": "Porto", "sl benfica": "Benfica", "sc braga": "Sp Braga", "braga": "Sp Braga",
        "vitoria sc": "Guimaraes", "v. guimaraes": "Guimaraes", "vitoria guimaraes": "Guimaraes",
        "estrela amadora": "Estrela", "estrela da amadora": "Estrela", "cf estrela": "Estrela",
        "avs futebol": "AVS", "afs": "AVS", "gil vicente fc": "Gil Vicente", "fc arouca": "Arouca",
        "fc famalicao": "Famalicao", "cd nacional": "Nacional", "casa pia ac": "Casa Pia",
        "cd santa clara": "Santa Clara", "rio ave fc": "Rio Ave", "moreirense fc": "Moreirense",
        "gd estoril": "Estoril", "estoril praia": "Estoril", "cd tondela": "Tondela", "fc alverca": "Alverca",
    },
    "E0": {
        "manchester city": "Man City", "man. city": "Man City",
        "manchester united": "Man United", "manchester utd": "Man United", "man. united": "Man United",
        "man. utd": "Man United", "man utd": "Man United",
        "nottingham forest": "Nott'm Forest", "nottingham": "Nott'm Forest", "nott. forest": "Nott'm Forest",
        "tottenham hotspur": "Tottenham", "spurs": "Tottenham", "west ham united": "West Ham",
        "wolverhampton": "Wolves", "wolverhampton wanderers": "Wolves", "newcastle united": "Newcastle",
        "brighton & hove albion": "Brighton", "brighton hove albion": "Brighton", "leeds united": "Leeds",
        "afc bournemouth": "Bournemouth", "ipswich town": "Ipswich", "hull city": "Hull",
        "coventry city": "Coventry", "leicester city": "Leicester",
    },
    "SP1": {
        "atletico madrid": "Ath Madrid", "atletico de madrid": "Ath Madrid", "atl. madrid": "Ath Madrid",
        "at. madrid": "Ath Madrid", "athletic bilbao": "Ath Bilbao", "athletic club": "Ath Bilbao",
        "athletic bilbau": "Ath Bilbao", "ath. bilbau": "Ath Bilbao", "real betis": "Betis",
        "celta vigo": "Celta", "celta de vigo": "Celta", "espanyol": "Espanol", "real sociedad": "Sociedad",
        "rayo vallecano": "Vallecano", "deportivo corunha": "La Coruna", "deportivo la coruna": "La Coruna",
        "corunha": "La Coruna", "sevilha": "Sevilla", "maiorca": "Mallorca", "racing santander": "Santander",
        "real oviedo": "Oviedo", "deportivo alaves": "Alaves",
    },
    "I1": {
        "inter milao": "Inter", "inter de milao": "Inter", "internazionale": "Inter", "inter milan": "Inter",
        "ac milan": "Milan", "milao": "Milan", "napoles": "Napoli", "as roma": "Roma", "bolonha": "Bologna",
        "genova": "Genoa", "hellas verona": "Verona", "veneza": "Venezia",
    },
    "D1": {
        "bayern munique": "Bayern Munich", "bayern": "Bayern Munich", "bayern munchen": "Bayern Munich",
        "borussia dortmund": "Dortmund", "b. dortmund": "Dortmund", "bayer leverkusen": "Leverkusen",
        "eintracht frankfurt": "Ein Frankfurt", "e. frankfurt": "Ein Frankfurt",
        "borussia monchengladbach": "M'gladbach", "b. monchengladbach": "M'gladbach",
        "monchengladbach": "M'gladbach", "colonia": "FC Koln", "fc colonia": "FC Koln", "koln": "FC Koln",
        "leipzig": "RB Leipzig", "schalke": "Schalke 04", "st. pauli": "St Pauli", "estugarda": "Stuttgart",
        "union berlim": "Union Berlin", "bremen": "Werder Bremen", "hamburgo": "Hamburg",
        "hamburger sv": "Hamburg", "mainz 05": "Mainz", "friburgo": "Freiburg", "augsburgo": "Augsburg",
        "wolfsburgo": "Wolfsburg",
    },
    "F1": {
        "paris saint-germain": "Paris SG", "paris saint germain": "Paris SG", "psg": "Paris SG",
        "marselha": "Marseille", "olympique marselha": "Marseille", "olympique lyon": "Lyon",
        "as monaco": "Monaco", "estrasburgo": "Strasbourg", "saint-etienne": "St Etienne",
        "as saint-etienne": "St Etienne",
    },
    "N1": {
        "psv": "PSV Eindhoven", "psv eindhoven": "PSV Eindhoven", "az": "AZ Alkmaar", "ajax amesterdao": "Ajax",
        "fortuna sittard": "For Sittard", "nec": "Nijmegen", "nec nijmegen": "Nijmegen", "pec zwolle": "Zwolle",
        "fc twente": "Twente", "fc utrecht": "Utrecht", "sc heerenveen": "Heerenveen", "fc groningen": "Groningen",
        "ado den haag": "Den Haag",
    },
    "B1": {
        "club bruges": "Club Brugge", "bruges": "Club Brugge", "brugge": "Club Brugge",
        "union saint-gilloise": "St. Gilloise", "union sg": "St. Gilloise", "union st. gilloise": "St. Gilloise",
        "standard liege": "Standard", "standard de liege": "Standard", "royal antwerp": "Antwerp",
        "ohl": "Oud-Heverlee Leuven", "leuven": "Oud-Heverlee Leuven", "sint-truiden": "St Truiden",
        "zulte waregem": "Waregem", "kaa gent": "Gent", "krc genk": "Genk", "kv mechelen": "Mechelen",
    },
    "T1": {
        "goztepe": "Goztep", "istanbul basaksehir": "Buyuksehyr", "basaksehir": "Buyuksehyr",
        "fatih karagumruk": "Karagumruk", "caykur rizespor": "Rizespor",
    },
    "G1": {
        "olympiacos": "Olympiakos", "olympiacos pireu": "Olympiakos", "olympiakos pireu": "Olympiakos",
        "aek atenas": "AEK", "aek athens": "AEK", "paok salonica": "PAOK", "paok salonika": "PAOK",
        "ofi creta": "OFI Crete", "aris salonica": "Aris",
    },
    "SC0": {"heart of midlothian": "Hearts", "glasgow rangers": "Rangers", "celtic glasgow": "Celtic"},
}


@dataclass(frozen=True)
class DomainSpec:
    version: str
    title: str  # shown in the criteria pop-up
    source: str  # data source description
    kind: str  # "elo" | "poisson": which explanation the pop-up shows
    load: Callable[[], list[data.Match]]
    make_model: Callable[[], object]
    build_kwargs: dict = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    code: str = ""  # football-data.co.uk league code; "" for national teams
    # Plain (lowercase, no accents) fragments of competition names, e.g. from the Santa Casa contest page.
    competitions: tuple[str, ...] = ()
    # Goal markets whose model beat the league's historical frequency in the backtest (docs/plano-competicoes.md).
    goal_markets: frozenset[str] = frozenset()


def _league(
    code: str,
    name: str,
    kind: str,
    competitions: tuple[str, ...] = (),
    goal_markets: tuple[str, ...] = (),
    aliases_of: str | None = None,  # lower divisions share the naming (and aliases) of their country's top league
) -> DomainSpec:
    model = (lambda: PoissonModel(use_h2h=True, dixon_coles=True)) if kind == "poisson" else OrderedLogitElo
    suffix = "poisson-h2h-dc-v1" if kind == "poisson" else "elo-logit-v1"
    return DomainSpec(
        version=f"{code.lower()}-{suffix}",
        title=name,
        source=f"Resultados da {name} das últimas 8 épocas (fonte: football-data.co.uk)",
        kind=kind,
        load=lambda: data.load_league(code, n_seasons=8),
        make_model=model,
        aliases=_CLUB_ALIASES.get(aliases_of or code, {}),
        code=code,
        competitions=(plain_name(name), *competitions),
        goal_markets=frozenset(goal_markets),
    )


NATIONS = DomainSpec(
    version="selecoes-poisson-h2h-dc-v1",
    title="Seleções nacionais",
    source="Resultados de jogos internacionais (fonte: martj42/international_results)",
    kind="poisson",
    load=lambda: data.load_international(since_year=datetime.now().year - 10),
    make_model=lambda: PoissonModel(use_h2h=True, dixon_coles=True),
    build_kwargs={"k": 40.0, "home_adv": 100.0, "season_regress": 0.0},
    competitions=(
        "liga das nacoes", "nations league", "mundial", "campeonato do mundo", "world cup", "europeu", "euro 20",
        "qualificacao", "apuramento", "amigavel", "particular", "copa america", "can 20",
    ),
    goal_markets=frozenset({"over25", "btts"}),
)

# Order matters when the competition is unknown: the first league where both teams are active wins.
LEAGUES = [
    _league("P1", "Primeira Liga", "elo", ("liga portugal", "i liga", "liga betclic", "liga nos"), ("over25", "btts")),
    _league("E0", "Premier League", "elo", ("liga inglesa", "inglaterra")),
    _league("SP1", "LaLiga", "elo", ("la liga", "liga espanhola", "primera division"), ("over25",)),
    _league("I1", "Serie A", "elo", ("liga italiana", "calcio"), ("btts",)),
    _league("D1", "Bundesliga", "poisson", ("liga alema", "1. bundesliga"), ("over25",)),
    _league("F1", "Ligue 1", "elo", ("liga francesa",), ("over25",)),
    _league("N1", "Eredivisie", "elo", ("liga neerlandesa", "liga holandesa", "paises baixos"), ("over25",)),
    _league("B1", "Liga belga", "elo", ("pro league", "jupiler", "belgica")),
    _league("T1", "Liga turca", "poisson", ("super lig", "turquia"), ("over25",)),
    _league("G1", "Liga grega", "elo", ("super league grecia", "grecia"), ("over25",)),
    _league("SC0", "Liga escocesa", "elo", ("premiership", "escocia"), ("over25", "btts")),
    # Second divisions (and below) after every top league.
    _league("E1", "Championship", "elo", ("inglaterra 2",), (), "E0"),
    _league("D2", "2. Bundesliga", "elo", ("bundesliga 2", "2 bundesliga", "alemanha 2"), (), "D1"),
    _league("SP2", "LaLiga 2", "poisson", ("la liga 2", "laliga hypermotion", "segunda division"), ("over25",), "SP1"),
    _league("I2", "Serie B", "elo", ("italia 2",), ("over25",), "I1"),
    _league("F2", "Ligue 2", "elo", ("franca 2",), (), "F1"),
    _league("E2", "League One", "elo", (), ("btts",), "E0"),
    _league("E3", "League Two", "elo", (), (), "E0"),
    _league("EC", "National League", "elo", (), ("over25", "btts"), "E0"),
    _league("SC1", "Championship escocesa", "elo", ("scottish championship",), (), "SC0"),
    _league("SC2", "League One escocesa", "elo", ("scottish league one",), ("over25",), "SC0"),
    _league("SC3", "League Two escocesa", "poisson", ("scottish league two",), ("over25", "btts"), "SC0"),
]

SPECS = {spec.version: spec for spec in [NATIONS, *LEAGUES]}
BY_CODE = {spec.code: spec for spec in LEAGUES}

# Competitions we recognise but do not model: they must not match a shorter covered name
# ("liga portugal 2" contains "liga portugal").
_UNCOVERED = ("liga portugal 2", "ii liga", "liga 2", "liga 3", "campeonato de portugal", "taca", "supertaca")
_COMPETITION_KEYS = sorted(
    [(key, spec) for spec in SPECS.values() for key in spec.competitions] + [(key, None) for key in _UNCOVERED],
    key=lambda kv: -len(kv[0]),
)


def spec_for_competition(name: str) -> DomainSpec | None:
    """The domain a competition name points to (most specific name wins), or None if unknown/uncovered."""
    plain = plain_name(name)
    return next((spec for key, spec in _COMPETITION_KEYS if key in plain), None) if plain else None


# A club is "active" in a league if it played there within this window of the league's last match,
# so relegated/promoted clubs are predicted in the division they play in now.
ACTIVE_WINDOW = timedelta(days=300)


@dataclass
class _TeamIndex:
    """Team names of a domain, available before (and without) training."""

    teams: dict[str, str]  # plain name -> dataset name
    games_played: Counter
    last_played: dict[str, datetime]
    latest: datetime  # date of the domain's last known match

    def active(self, team: str) -> bool:
        return self.latest - self.last_played[team] <= ACTIVE_WINDOW

    def resolve(self, name: str, aliases: dict[str, str]) -> str | None:
        plain = plain_name(name)
        if plain in aliases:
            return aliases[plain]
        if plain in self.teams:
            return self.teams[plain]
        close = difflib.get_close_matches(plain, self.teams.keys(), n=1, cutoff=0.85)
        return self.teams[close[0]] if close else None


@dataclass
class _Domain:
    spec: DomainSpec
    matches: list[data.Match]
    model: object
    state: FeatureState  # after the last known result: features of new fixtures come from here
    weights: dict[str, float]  # criterion id -> share of influence
    neutral: dict[str, float]  # "no information" value per feature, for user-scaled criteria
    rows: Rows  # training rows: the goal model of Elo domains is fitted on them when first needed
    goal_freq: dict[str, float]  # how often each goal market happened in recent games of the league
    trained_at: datetime = field(default_factory=datetime.now)


def _matches(spec: DomainSpec) -> list[data.Match]:
    return _cache.get_or_set(f"matches:{spec.version}", spec.load)


def _team_index(spec: DomainSpec) -> _TeamIndex:
    def build() -> _TeamIndex:
        matches = _matches(spec)  # chronological, so later dates overwrite earlier ones
        return _TeamIndex(
            {plain_name(t): t for m in matches for t in (m.home, m.away)},
            Counter(t for m in matches for t in (m.home, m.away)),
            {t: m.date for m in matches for t in (m.home, m.away)},
            matches[-1].date,
        )

    return _cache.get_or_set(f"teams:{spec.version}", build)


def _domain(spec: DomainSpec) -> _Domain:
    def train() -> _Domain:
        matches = _matches(spec)
        rows, state = build_rows_and_state(matches, **spec.build_kwargs)
        eligible = rows.eligible.nonzero()[0]
        model = spec.make_model()
        model.fit(rows.subset(eligible))
        recent = rows.subset(eligible[-1000:])  # recent games: today's influence
        total = recent.home_goals + recent.away_goals
        goal_freq = {
            "over25": float((total >= 3).mean()),
            "btts": float(((recent.home_goals > 0) & (recent.away_goals > 0)).mean()),
        }
        return _Domain(
            spec, matches, model, state, criteria_weights(model, recent), neutral_values(recent),
            rows.subset(eligible), goal_freq,
        )

    return _cache.get_or_set(f"domain:{spec.version}", train)


def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None  # data source down: callers fall back to other models


def model_info(version: str) -> dict | None:
    """Fitted weights and training data summary of a trained model (trains it if needed)."""
    spec = SPECS.get(version)
    domain = _safe(_domain, spec) if spec else None
    if domain is None:
        return None
    return {
        "title": spec.title,
        "source": spec.source,
        "kind": spec.kind,
        "weights": domain.weights,
        "n_matches": len(domain.matches),
        "data_from": domain.matches[0].date.date(),
        "data_to": domain.matches[-1].date.date(),
        "trained_at": domain.trained_at,
    }


def _nation_alias(name: str) -> str | None:
    plain = plain_name(name)
    en = next((v for k, v in _PT_TO_EN.items() if plain_name(k) == plain), None)
    return _NATIONS_DATASET_ALIASES.get(en, en) if en else None


def _fixture_rows(domain: _Domain, fixtures: list[tuple[str, str]], multipliers: dict[str, float] | None) -> Rows:
    """Features come from the state after the last known result; fixtures never update it."""
    now = datetime.now()
    upcoming = [data.Match(now, home, away, 0, 0) for home, away in fixtures]
    return apply_multipliers(fixture_rows(domain.state, upcoming), multipliers or {}, domain.neutral)


def _predict_fixtures(
    domain: _Domain, fixtures: list[tuple[str, str]], multipliers: dict[str, float] | None = None
) -> list[Probs]:
    probs = domain.model.predict(_fixture_rows(domain, fixtures, multipliers))
    return [(float(p[0]), float(p[1]), float(p[2])) for p in probs]


def _goals_model(domain: _Domain) -> PoissonModel:
    """The domain's own model when it is a goal model; otherwise a plain Poisson fitted on the same games."""
    if isinstance(domain.model, PoissonModel):
        return domain.model

    def fit() -> PoissonModel:
        model = PoissonModel()
        model.fit(domain.rows)
        return model

    return _cache.get_or_set(f"goals:{domain.spec.version}", fit)


@dataclass
class Forecast:
    probs: Probs
    version: str
    expected_goals: tuple[float, float]
    # market -> (probability, True if it comes from the model, False if it is the league's historical frequency)
    goal_markets: dict[str, tuple[float, bool]]
    # Extra goal lines straight from the score grid, not backtested against the league average
    # (informational only, like expected_goals and top_scores): over15, over35.
    other_goal_lines: dict[str, float]
    top_scores: list[tuple[int, int, float]]  # most likely exact scores: (home goals, away goals, probability)


def forecast_league(
    code: str, pairs: list[tuple[str, str]], multipliers: dict[str, float] | None = None
) -> list[Forecast | None]:
    """1X2 and goal forecasts for fixtures of a known league (names as in football-data.co.uk).

    `multipliers` ({criterion id: 0..2}) scale the criteria, same as in predict_many.
    None for a fixture whose teams have too few games in that league. Raises if the league data is unavailable.
    """
    spec = BY_CODE[code]
    index = _team_index(spec)
    known = {}
    for i, (home_name, away_name) in enumerate(pairs):
        home, away = index.resolve(home_name, spec.aliases), index.resolve(away_name, spec.aliases)
        if home and away and home != away and min(index.games_played[home], index.games_played[away]) >= MIN_PRIOR_GAMES:
            known[i] = (home, away)
    out: list[Forecast | None] = [None] * len(pairs)
    if not known:
        return out

    domain = _domain(spec)
    rows = _fixture_rows(domain, list(known.values()), multipliers)
    probs = domain.model.predict(rows)
    grids = _goals_model(domain).score_grid(rows)
    model_markets = _goals_model(domain).goal_markets(rows)
    goals = np.arange(MAX_GOALS + 1)
    for j, i in enumerate(known):
        grid = grids[j]
        top = np.argsort(grid, axis=None)[::-1][:3]
        out[i] = Forecast(
            probs=(float(probs[j][0]), float(probs[j][1]), float(probs[j][2])),
            version=spec.version,
            expected_goals=(float(grid.sum(axis=1) @ goals), float(grid.sum(axis=0) @ goals)),
            goal_markets={
                market: (float(model_markets[market][j]), True)
                if market in spec.goal_markets
                else (domain.goal_freq[market], False)
                for market in ("over25", "btts")
            },
            other_goal_lines={
                market: float(model_markets[market][j]) for market in ("over15", "over35")
            },
            top_scores=[(int(h), int(a), float(grid[h, a])) for h, a in zip(*np.unravel_index(top, grid.shape))],
        )
    return out


def _names(spec: DomainSpec, pair: tuple[str, str]) -> tuple[str | None, str | None]:
    if spec is NATIONS:
        return _nation_alias(pair[0]), _nation_alias(pair[1])
    return pair


def _predict_in(spec, pending, pairs, results, multipliers, require_active: bool) -> set[int]:
    """Predict, with `spec`'s model, the pending pairs whose two teams it knows; returns the indices done."""
    candidates = {i: _names(spec, pairs[i]) for i in pending}
    candidates = {i: names for i, names in candidates.items() if all(names)}
    if not candidates:
        return set()  # e.g. no national teams: don't even load that dataset
    index = _safe(_team_index, spec)
    if index is None:
        return set()
    known = {}
    for i, (home_name, away_name) in candidates.items():
        home, away = index.resolve(home_name, spec.aliases), index.resolve(away_name, spec.aliases)
        if not (home and away) or home == away:
            continue
        if min(index.games_played[home], index.games_played[away]) < MIN_PRIOR_GAMES:
            continue
        if require_active and not (index.active(home) and index.active(away)):
            continue
        known[i] = (home, away)
    if not known:
        return set()  # nothing for this domain: skip training it
    domain = _safe(_domain, spec)
    if domain is None:
        return set()
    for i, probs in zip(known, _predict_fixtures(domain, list(known.values()), multipliers)):
        results[i] = (probs, spec.version)
    return set(known)


def predict_many(
    pairs: list[tuple[str, str]],
    multipliers: dict[str, float] | None = None,
    competitions: list[str] | None = None,
) -> list[tuple[Probs, str] | None]:
    """For each (home, away): ((p_home, p_draw, p_away), model_version), or None if no domain knows both teams.

    `competitions` (optional, one name per pair) sends a match to that competition's model first.
    `multipliers` ({criterion id: 0..2}) scale the criteria of the trained models; None keeps the defaults.
    """
    results: list[tuple[Probs, str] | None] = [None] * len(pairs)

    hinted: dict[str, list[int]] = defaultdict(list)
    for i, name in enumerate(competitions or []):
        spec = spec_for_competition(name)
        if spec:
            hinted[spec.version].append(i)
    for version, indices in hinted.items():
        _predict_in(SPECS[version], indices, pairs, results, multipliers, require_active=False)

    pending = [i for i in range(len(pairs)) if results[i] is None]
    for spec in [NATIONS, *LEAGUES]:
        if not pending:
            break
        done = _predict_in(spec, pending, pairs, results, multipliers, require_active=spec is not NATIONS)
        pending = [i for i in pending if i not in done]
    return results
