"""Run with: python -m unittest tests.test_engine"""

import unittest

from pydantic import ValidationError

from app.models import DesdobramentoRequest, MatchInput, ResultProbabilities
from app.services.totobola_engine import _apply_double, _double_counts


def _probs(home: float, draw: float, away: float) -> ResultProbabilities:
    return ResultProbabilities(
        match_id="m", home_team="A", away_team="B", prob_home=home, prob_draw=draw, prob_away=away, criteria_breakdown={}
    )


class DoubleTest(unittest.TestCase):
    def test_excluded_share_is_split_proportionally(self):
        p = _apply_double(_probs(0.3341, 0.2842, 0.3816), ["1", "X"])
        self.assertEqual(p.prob_away, 0.0)
        self.assertAlmostEqual(p.prob_home, 0.3341 / (0.3341 + 0.2842), places=4)
        self.assertAlmostEqual(p.prob_home + p.prob_draw, 1.0, places=3)
        self.assertEqual(p.probs_modelo, [0.3341, 0.2842, 0.3816])

    def test_both_chosen_outcomes_get_bets(self):
        counts = _double_counts({"1": 0.95, "X": 0.05, "2": 0.0}, ["1", "X"], 4)
        self.assertEqual(counts, {"1": 3, "X": 1, "2": 0})

    def test_single_bet_takes_the_likelier_outcome(self):
        counts = _double_counts({"1": 0.3, "X": 0.0, "2": 0.7}, ["1", "2"], 1)
        self.assertEqual(counts, {"1": 0, "X": 0, "2": 1})

    def test_picks_are_validated(self):
        base = dict(id="m", home_team="A", away_team="B", home_country="", away_country="")
        with self.assertRaises(ValidationError):
            MatchInput(**base, fixed_results=["1", "1"])
        with self.assertRaises(ValidationError):
            MatchInput(**base, fixed_results=["1", "X", "2"])


if __name__ == "__main__":
    unittest.main()



class CompetitionRoutingTest(unittest.TestCase):
    def test_most_specific_competition_name_wins(self):
        from app.services.trained_model import NATIONS, spec_for_competition

        self.assertIs(spec_for_competition("Liga das Nações"), NATIONS)
        self.assertEqual(spec_for_competition("Liga Portugal Betclic").code, "P1")
        self.assertIsNone(spec_for_competition("Liga Portugal 2"))  # not modelled: must not fall into P1
        self.assertIsNone(spec_for_competition("Taça de Portugal"))
        self.assertIsNone(spec_for_competition(""))

    def test_a_club_is_active_only_if_it_played_there_last_season(self):
        from collections import Counter
        from datetime import datetime

        from app.services.trained_model import _TeamIndex

        index = _TeamIndex(
            {}, Counter(), {"Stayed": datetime(2026, 9, 20), "Relegated": datetime(2025, 5, 18)}, datetime(2026, 9, 21)
        )
        self.assertTrue(index.active("Stayed"))
        self.assertFalse(index.active("Relegated"))
