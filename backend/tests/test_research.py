"""Run with: python -m unittest discover -s tests"""

import unittest
from dataclasses import replace
from typing import get_args
from datetime import datetime, timedelta

import numpy as np

from app.models import CriterionId, DesdobramentoRequest
from app.research import metrics
from app.research.data import Match
from app.research.features import build_rows, build_rows_and_state, fixture_rows
from app.research.importance import CRITERIA, apply_multipliers, neutral_values
from app.research.models import PoissonModel


def _synthetic_matches(n: int = 400, seed: int = 0) -> list[Match]:
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(10)]
    strength = {t: rng.normal(0, 0.4) for t in teams}
    start = datetime(2020, 8, 1)
    matches = []
    for i in range(n):
        home, away = rng.choice(teams, size=2, replace=False)
        lam = np.exp(0.3 + strength[home] - strength[away])
        mu = np.exp(0.1 + strength[away] - strength[home])
        matches.append(Match(start + timedelta(days=i), home, away, int(rng.poisson(lam)), int(rng.poisson(mu))))
    return matches


class NoLookAheadTest(unittest.TestCase):
    def test_changing_a_future_result_does_not_change_past_features(self):
        matches = _synthetic_matches()
        cut = 250
        altered = matches[:cut] + [replace(m, home_goals=m.home_goals + 5) for m in matches[cut:]]
        a, b = build_rows(matches), build_rows(altered)
        for field in ("elo_diff", "home_for", "home_against", "away_for", "away_against", "h2h"):
            # Features of match `cut` itself are pre-match, so they must match too.
            np.testing.assert_array_equal(getattr(a, field)[: cut + 1], getattr(b, field)[: cut + 1], field)


class FixtureStateTest(unittest.TestCase):
    def test_fixture_features_match_appending_the_fixture_to_history(self):
        matches = _synthetic_matches(n=300)
        fixture = Match(matches[-1].date + timedelta(days=1), "T1", "T2", 0, 0)  # same season
        _, state = build_rows_and_state(matches)
        from_state = fixture_rows(state, [fixture])
        appended = build_rows(matches + [fixture]).subset([len(matches)])
        for field in ("elo_diff", "home_for", "home_against", "away_for", "away_against", "h2h", "eligible"):
            np.testing.assert_array_equal(getattr(from_state, field), getattr(appended, field), field)


class PoissonModelTest(unittest.TestCase):
    def test_probabilities_are_valid_and_beat_uniform(self):
        matches = _synthetic_matches(n=1500)
        rows = build_rows(matches)
        train = rows.subset(np.arange(0, 1200))
        test = rows.subset(np.arange(1200, 1500))
        model = PoissonModel(dixon_coles=True)
        model.fit(train)
        probs = model.predict(test)
        np.testing.assert_allclose(probs.sum(axis=1), 1.0, atol=1e-9)
        self.assertTrue((probs > 0).all())
        uniform = np.full_like(probs, 1 / 3)
        self.assertLess(metrics.log_loss(probs, test.outcome), metrics.log_loss(uniform, test.outcome))

    def test_goal_markets_come_from_the_same_score_grid(self):
        rows = build_rows(_synthetic_matches(n=800))
        model = PoissonModel(dixon_coles=True)
        model.fit(rows.subset(np.arange(0, 700)))
        test = rows.subset(np.arange(700, 800))
        grid = model.score_grid(test)
        np.testing.assert_allclose(grid.sum(axis=(1, 2)), 1.0, atol=1e-9)
        markets = model.goal_markets(test)
        under = grid[:, 0, 0] + grid[:, 1, 0] + grid[:, 0, 1] + grid[:, 2, 0] + grid[:, 1, 1] + grid[:, 0, 2]
        np.testing.assert_allclose(markets["over25"], 1 - under, atol=1e-9)
        no_btts = grid[:, 0, :].sum(axis=1) + grid[:, :, 0].sum(axis=1) - grid[:, 0, 0]
        np.testing.assert_allclose(markets["btts"], 1 - no_btts, atol=1e-9)


class MetricsTest(unittest.TestCase):
    def test_perfect_forecast(self):
        y = np.array([0, 1, 2])
        p = np.eye(3)
        self.assertAlmostEqual(metrics.rps(p, y), 0.0)
        self.assertAlmostEqual(metrics.brier(p, y), 0.0)
        self.assertLess(metrics.log_loss(p, y), 1e-9)


if __name__ == "__main__":
    unittest.main()


class MultipliersTest(unittest.TestCase):
    def setUp(self):
        matches = _synthetic_matches(n=1200)
        rows, self.state = build_rows_and_state(matches)
        train = rows.subset(rows.eligible.nonzero()[0])
        self.model = PoissonModel()
        self.model.fit(train)
        self.neutral = neutral_values(train)
        self.fixture = fixture_rows(self.state, [Match(matches[-1].date + timedelta(days=1), "T1", "T2", 0, 0)])

    def predict(self, multipliers):
        return self.model.predict(apply_multipliers(self.fixture, multipliers, self.neutral))[0]

    def test_all_ones_is_exactly_the_default(self):
        np.testing.assert_array_equal(self.predict({c: 1.0 for c in CRITERIA}), self.predict({}))

    def test_zero_sets_the_neutral_value_and_two_doubles_the_gap(self):
        for m in (0.0, 2.0):
            scaled = apply_multipliers(self.fixture, {"ataque": m}, self.neutral)
            for f in ("home_for", "away_for"):
                gap = getattr(self.fixture, f) - self.neutral[f]
                np.testing.assert_allclose(getattr(scaled, f) - self.neutral[f], m * gap)

    def test_every_criterion_changes_a_single_fixture(self):
        # The neutral value comes from training, not from the fixtures, so one fixture is enough.
        for criterion in ("elo", "ataque", "defesa"):
            self.assertFalse(np.allclose(self.predict({criterion: 0.0}), self.predict({})), criterion)

    def test_api_accepts_only_known_criteria_in_range(self):
        self.assertEqual(set(get_args(CriterionId)), set(CRITERIA))
        DesdobramentoRequest(matches=[], n_apostas=1, multiplicadores={"elo": 2, "casa": 0})
        for bad in ({"elo": 2.1}, {"elo": -0.1}, {"forma": 1}):
            with self.assertRaises(ValueError):
                DesdobramentoRequest(matches=[], n_apostas=1, multiplicadores=bad)
