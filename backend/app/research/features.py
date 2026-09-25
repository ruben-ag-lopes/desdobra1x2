"""Pre-match features computed strictly chronologically (no look-ahead).

Row i only uses matches with index < i, so it is safe to train on rows whose
matches finished before a given test match.
"""

from collections import defaultdict, deque
from dataclasses import dataclass

import numpy as np

from app.research.data import Match

INITIAL_ELO = 1500.0
MIN_PRIOR_GAMES = 5
LEAGUE_AVG_GOALS = 1.3  # prior for teams with no history yet

_FEATURES = ("elo_diff", "home_for", "home_against", "away_for", "away_against", "home_field", "h2h")


@dataclass
class Rows:
    """Feature matrix aligned with the (chronological) match list."""

    elo_diff: np.ndarray  # home Elo - away Elo, before the match
    home_for: np.ndarray  # home team avg goals scored, last N games (any venue)
    home_against: np.ndarray
    away_for: np.ndarray
    away_against: np.ndarray
    home_field: np.ndarray  # 1 = real home game, 0 = neutral venue
    h2h: np.ndarray  # avg goal difference (home perspective) in last <=5 meetings, 0 if none
    home_goals: np.ndarray
    away_goals: np.ndarray
    outcome: np.ndarray  # 0/1/2
    eligible: np.ndarray  # both teams have >= MIN_PRIOR_GAMES prior games

    def subset(self, idx: np.ndarray) -> "Rows":
        return Rows(**{k: v[idx] for k, v in self.__dict__.items()})


class FeatureState:
    """Ratings, recent form and head-to-head history after the matches seen so far."""

    def __init__(self, k: float = 25.0, home_adv: float = 60.0, form_n: int = 8, season_regress: float = 0.25):
        self.k = k
        self.home_adv = home_adv
        self.season_regress = season_regress
        self.elo: dict[str, float] = defaultdict(lambda: INITIAL_ELO)
        self.history: dict[str, deque] = defaultdict(lambda: deque(maxlen=form_n))  # (goals_for, goals_against)
        self.played: dict[str, int] = defaultdict(int)
        self.meetings: dict[tuple[str, str], deque] = defaultdict(lambda: deque(maxlen=5))
        self.season: int | None = None

    def start_match_day(self, m: Match) -> None:
        """New season starts in July/August: pull ratings towards the mean (promotions, transfers)."""
        season = m.date.year if m.date.month >= 7 else m.date.year - 1
        if self.season_regress and self.season is not None and season != self.season:
            for team in list(self.elo):
                self.elo[team] += self.season_regress * (INITIAL_ELO - self.elo[team])
        self.season = season

    def features(self, m: Match) -> dict[str, float]:
        hist_h, hist_a = self.history.get(m.home), self.history.get(m.away)
        past = self.meetings.get(tuple(sorted((m.home, m.away))))
        return {
            "elo_diff": self.elo.get(m.home, INITIAL_ELO) - self.elo.get(m.away, INITIAL_ELO),
            "home_field": 0.0 if m.neutral else 1.0,
            "home_for": np.mean([g[0] for g in hist_h]) if hist_h else LEAGUE_AVG_GOALS,
            "home_against": np.mean([g[1] for g in hist_h]) if hist_h else LEAGUE_AVG_GOALS,
            "away_for": np.mean([g[0] for g in hist_a]) if hist_a else LEAGUE_AVG_GOALS,
            "away_against": np.mean([g[1] for g in hist_a]) if hist_a else LEAGUE_AVG_GOALS,
            "h2h": np.mean([d if h == m.home else -d for h, d in past]) if past else 0.0,
        }

    def eligible(self, m: Match) -> bool:
        return self.played.get(m.home, 0) >= MIN_PRIOR_GAMES and self.played.get(m.away, 0) >= MIN_PRIOR_GAMES

    def update(self, m: Match) -> None:
        """Apply a finished match's result."""
        elo = self.elo
        adv = 0.0 if m.neutral else self.home_adv
        expected_home = 1 / (1 + 10 ** (-(elo[m.home] - elo[m.away] + adv) / 400))
        score_home = {0: 1.0, 1: 0.5, 2: 0.0}[m.outcome]
        gd = abs(m.home_goals - m.away_goals)
        multiplier = 1.0 if gd <= 1 else (1.5 if gd == 2 else (11 + gd) / 8)
        delta = self.k * multiplier * (score_home - expected_home)
        elo[m.home] += delta
        elo[m.away] -= delta
        self.history[m.home].append((m.home_goals, m.away_goals))
        self.history[m.away].append((m.away_goals, m.home_goals))
        self.played[m.home] += 1
        self.played[m.away] += 1
        self.meetings[tuple(sorted((m.home, m.away)))].append((m.home, m.home_goals - m.away_goals))


def _rows(feature_dicts: list[dict], matches: list[Match], eligible: list[bool]) -> Rows:
    cols = {name: np.array([f[name] for f in feature_dicts], dtype=float) for name in _FEATURES}
    return Rows(
        home_goals=np.array([m.home_goals for m in matches], dtype=float),
        away_goals=np.array([m.away_goals for m in matches], dtype=float),
        outcome=np.array([m.outcome for m in matches], dtype=int),
        eligible=np.array(eligible, dtype=bool),
        **cols,
    )


def build_rows_and_state(
    matches: list[Match],
    k: float = 25.0,
    home_adv: float = 60.0,
    form_n: int = 8,
    season_regress: float = 0.25,
) -> tuple[Rows, FeatureState]:
    """Pre-match features of every match, plus the state after the last one (for new fixtures).

    `season_regress` pulls ratings towards the mean each July (clubs only; use 0 for national teams).
    """
    state = FeatureState(k, home_adv, form_n, season_regress)
    features, eligible = [], []
    for m in matches:
        state.start_match_day(m)
        features.append(state.features(m))
        eligible.append(state.eligible(m))
        state.update(m)  # after the features were stored
    return _rows(features, matches, eligible), state


def build_rows(matches: list[Match], **kwargs) -> Rows:
    return build_rows_and_state(matches, **kwargs)[0]


def fixture_rows(state: FeatureState, fixtures: list[Match]) -> Rows:
    """Features of upcoming fixtures from a state; the fixtures never update it."""
    return _rows([state.features(m) for m in fixtures], fixtures, [state.eligible(m) for m in fixtures])
