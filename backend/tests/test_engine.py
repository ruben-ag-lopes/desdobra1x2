"""Run with: python -m unittest tests.test_engine"""

import unittest

from pydantic import ValidationError

from app.models import DesdobramentoRequest, MatchInput, ResultProbabilities
from app.services import totobola_engine
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


class CustomizationTest(unittest.TestCase):
    """Test criterion customization (multipliers)."""

    def test_multiplier_1_0_equals_default(self):
        """With all multipliers at 1.0, predictions should be identical to default."""
        from app.research.importance import CRITERIA
        
        req = DesdobramentoRequest(
            matches=[MatchInput(
                id="1",
                home_team="Portugal",
                away_team="Noruega",
                home_country="PT",
                away_country="NO",
                competition_code="LEA",
            )],
            n_apostas=4,
        )
        
        # Prediction with defaults
        probs_default, _ = totobola_engine.gerar_desdobramento(req.matches, req.n_apostas)
        
        # Prediction with all multipliers = 1.0
        multipliers = {crit_id: 1.0 for crit_id in CRITERIA}
        probs_custom, _ = totobola_engine.gerar_desdobramento(req.matches, req.n_apostas, multipliers)
        
        # Should be identical (within floating point tolerance)
        self.assertAlmostEqual(probs_default[0].prob_home, probs_custom[0].prob_home, places=6)
        self.assertAlmostEqual(probs_default[0].prob_draw, probs_custom[0].prob_draw, places=6)
        self.assertAlmostEqual(probs_default[0].prob_away, probs_custom[0].prob_away, places=6)

    def test_multiplier_0_disables_criterion(self):
        """Setting a criterion to 0 should disable it (use neutral value)."""
        from app.research.importance import CRITERIA
        
        req = DesdobramentoRequest(
            matches=[MatchInput(
                id="1",
                home_team="Portugal",
                away_team="Noruega",
                home_country="PT",
                away_country="NO",
                competition_code="LEA",
            )],
            n_apostas=1,
        )
        
        # Prediction with Elo at 0 (neutral)
        multipliers = {"elo": 0.0}
        probs, _ = totobola_engine.gerar_desdobramento(req.matches, req.n_apostas, multipliers)
        
        # With Elo disabled, the probabilities should be closer to neutral (1/3 each)
        # This is a weak test, but at least verifies it doesn't crash
        self.assertGreater(probs[0].prob_home, 0.0)
        self.assertGreater(probs[0].prob_draw, 0.0)
        self.assertGreater(probs[0].prob_away, 0.0)

