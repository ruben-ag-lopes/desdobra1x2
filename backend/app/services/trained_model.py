"""Production 1X2 predictions from models fitted on historical results.

One "domain" per team pool (national teams, or one domestic league). Each domain
uses the model that won its walk-forward backtest (`python -m app.research.backtest`,
results in docs/plano-competicoes.md); when two models were within 0.002 log loss,
the simpler Elo model is kept. Domains are trained lazily, only when a fixture
needs them, and refitted at most every 12h on data that includes the latest results.
"""

import difflib
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from app.cache import TTLCache
from app.research import data
from app.research.features import MIN_PRIOR_GAMES, FeatureState, build_rows_and_state, fixture_rows
from app.research.importance import apply_multipliers, criteria_weights, neutral_values
from app.research.models import OrderedLogitElo, PoissonModel
from app.scrapers.elo_ratings import _PT_TO_EN

_cache = TTLCache(ttl_seconds=12 * 3600)

Probs = tuple[float, float, float]


def _plain(name: str) -> str:
    stripped = "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")
    return " ".join(stripped.lower().split())


# eloratings.net-style English names (from _PT_TO_EN) -> martj42 dataset names
_NATIONS_DATASET_ALIASES = {"Czechia": "Czech Republic", "Ireland": "Republic of Ireland"}

# Santa Casa / Portuguese / full club names -> football-data.co.uk names, keyed by _plain(name).
# Names that already match the dataset (after _plain) or are within the fuzzy cutoff need no entry.
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
        "as monaco": "Monaco", "estrasburgo": "Strasbourg",
    },
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


def _league(code: str, name: str, kind: str) -> DomainSpec:
    model = (lambda: PoissonModel(use_h2h=True, dixon_coles=True)) if kind == "poisson" else OrderedLogitElo
    suffix = "poisson-h2h-dc-v1" if kind == "poisson" else "elo-logit-v1"
    return DomainSpec(
        version=f"{code.lower()}-{suffix}",
        title=name,
        source=f"Resultados da {name} das últimas 8 épocas (fonte: football-data.co.uk)",
        kind=kind,
        load=lambda: data.load_league(code, n_seasons=8),
        make_model=model,
        aliases=_CLUB_ALIASES.get(code, {}),
    )


NATIONS = DomainSpec(
    version="selecoes-poisson-h2h-dc-v1",
    title="Seleções nacionais",
    source="Resultados de jogos internacionais (fonte: martj42/international_results)",
    kind="poisson",
    load=lambda: data.load_international(since_year=datetime.now().year - 10),
    make_model=lambda: PoissonModel(use_h2h=True, dixon_coles=True),
    build_kwargs={"k": 40.0, "home_adv": 100.0, "season_regress": 0.0},
)

# Order matters: the first league that knows both teams wins.
LEAGUES = [
    _league("P1", "Primeira Liga", "elo"),
    _league("E0", "Premier League", "elo"),
    _league("SP1", "LaLiga", "elo"),
    _league("I1", "Serie A", "elo"),
    _league("D1", "Bundesliga", "poisson"),
    _league("F1", "Ligue 1", "elo"),
]

SPECS = {spec.version: spec for spec in [NATIONS, *LEAGUES]}


@dataclass
class _TeamIndex:
    """Team names of a domain, available before (and without) training."""

    teams: dict[str, str]  # plain name -> dataset name
    games_played: Counter

    def resolve(self, name: str, aliases: dict[str, str]) -> str | None:
        plain = _plain(name)
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
    trained_at: datetime = field(default_factory=datetime.now)


def _matches(spec: DomainSpec) -> list[data.Match]:
    return _cache.get_or_set(f"matches:{spec.version}", spec.load)


def _team_index(spec: DomainSpec) -> _TeamIndex:
    def build() -> _TeamIndex:
        matches = _matches(spec)
        return _TeamIndex(
            {_plain(t): t for m in matches for t in (m.home, m.away)},
            Counter(t for m in matches for t in (m.home, m.away)),
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
        return _Domain(spec, matches, model, state, criteria_weights(model, recent), neutral_values(recent))

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
    plain = _plain(name)
    en = next((v for k, v in _PT_TO_EN.items() if _plain(k) == plain), None)
    return _NATIONS_DATASET_ALIASES.get(en, en) if en else None


def _predict_fixtures(
    domain: _Domain, fixtures: list[tuple[str, str]], multipliers: dict[str, float] | None = None
) -> list[Probs]:
    """Features come from the state after the last known result; fixtures never update it."""
    now = datetime.now()
    upcoming = [data.Match(now, home, away, 0, 0) for home, away in fixtures]
    rows = apply_multipliers(fixture_rows(domain.state, upcoming), multipliers or {}, domain.neutral)
    probs = domain.model.predict(rows)
    return [(float(p[0]), float(p[1]), float(p[2])) for p in probs]


def predict_many(
    pairs: list[tuple[str, str]], multipliers: dict[str, float] | None = None
) -> list[tuple[Probs, str] | None]:
    """For each (home, away): ((p_home, p_draw, p_away), model_version), or None if no domain knows both teams.

    `multipliers` ({criterion id: 0..2}) scale the criteria of the trained models; None keeps the defaults.
    """
    results: list[tuple[Probs, str] | None] = [None] * len(pairs)
    pending = list(range(len(pairs)))

    nation_names = {i: (_nation_alias(pairs[i][0]), _nation_alias(pairs[i][1])) for i in pending}
    candidates = [(NATIONS, lambda i: nation_names[i])] + [(spec, lambda i: pairs[i]) for spec in LEAGUES]
    for spec, names_of in candidates:
        if not pending:
            break
        if spec is NATIONS and not any(all(nation_names[i]) for i in pending):
            continue  # no national-team fixtures: don't even load that dataset
        index = _safe(_team_index, spec)
        if index is None:
            continue
        known = {}
        for i in pending:
            home_name, away_name = names_of(i)
            if not (home_name and away_name):
                continue
            home, away = index.resolve(home_name, spec.aliases), index.resolve(away_name, spec.aliases)
            played = min(index.games_played[home], index.games_played[away]) if home and away else 0
            if home != away and played >= MIN_PRIOR_GAMES:
                known[i] = (home, away)
        if not known:
            continue  # nothing for this domain: skip training it
        domain = _safe(_domain, spec)
        if domain is None:
            continue
        for i, probs in zip(known, _predict_fixtures(domain, list(known.values()), multipliers)):
            results[i] = (probs, spec.version)
        pending = [i for i in pending if i not in known]
    return results
