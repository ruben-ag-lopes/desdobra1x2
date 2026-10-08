"""Run with: python -m unittest tests.test_trained_criteria

Elo-kind leagues use only two criteria (strength, home advantage). The user must still be able to
customise all five, without the numbers jumping between two model families (app/services/trained_model._probs).
"""

import unittest

import numpy as np

from app.research.features import build_rows_and_state
from app.research.importance import criteria_weights, neutral_values
from app.research.models import OrderedLogitElo
from app.services import trained_model as tm
from tests.test_research import _synthetic_matches


def _elo_domain() -> tm._Domain:
    matches = _synthetic_matches(n=900)
    rows, state = build_rows_and_state(matches)
    train = rows.subset(rows.eligible.nonzero()[0])
    model = OrderedLogitElo()
    model.fit(train)
    spec = tm.DomainSpec(
        version="synthetic-elo-logit-v1", title="Sintético", source="teste", kind="elo",
        load=lambda: matches, make_model=OrderedLogitElo,
    )
    return tm._Domain(spec, matches, model, state, criteria_weights(model, train), neutral_values(train), train, {})


class EloDomainCustomCriteriaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.domain = _elo_domain()
        cls.fixtures = [("T1", "T2"), ("T3", "T4"), ("T5", "T6")]
        cls.default = tm._probs(cls.domain, cls.fixtures, None)

    def test_no_customisation_is_exactly_the_validated_model(self):
        plain = self.domain.model.predict(tm._fixture_rows(self.domain, self.fixtures, None))
        np.testing.assert_array_equal(self.default, plain)

    def test_the_validated_models_own_weights_change_nothing(self):
        base = tm._base_multipliers(self.domain)
        np.testing.assert_allclose(tm._probs(self.domain, self.fixtures, base), self.default, atol=1e-9)
        self.assertEqual({k for k, v in base.items() if v == 0}, {"ataque", "defesa", "h2h"} - set(self.domain.weights))

    def test_a_criterion_left_out_stays_out(self):
        # Elo and home advantage only, exactly as the validated model weighs them, with the rest at 0.
        base = tm._base_multipliers(self.domain)
        left_out = {**base, "h2h": 0.0, "ataque": 0.0, "defesa": 0.0}
        np.testing.assert_allclose(tm._probs(self.domain, self.fixtures, left_out), self.default, atol=1e-9)

    def test_criteria_the_elo_model_ignores_now_have_an_effect(self):
        base = tm._base_multipliers(self.domain)
        for criterion in ("ataque", "defesa", "h2h"):
            custom = tm._probs(self.domain, self.fixtures, {**base, criterion: 0.8})
            self.assertFalse(np.allclose(custom, self.default, atol=1e-6), f"{criterion} had no effect")

    def test_a_small_change_gives_a_small_move_not_a_model_jump(self):
        custom = tm._probs(self.domain, self.fixtures, {**tm._base_multipliers(self.domain), "ataque": 0.1})
        self.assertLess(np.abs(custom - self.default).max(), 0.05)

    def test_probabilities_stay_valid(self):
        custom = tm._probs(self.domain, self.fixtures, {"elo": 0.1, "casa": 1.0, "ataque": 0.9, "h2h": 0.9})
        np.testing.assert_allclose(custom.sum(axis=1), 1.0)
        self.assertTrue((custom > 0).all())

    def test_the_full_model_reports_weights_for_all_five_criteria(self):
        weights = tm._full(self.domain).weights
        self.assertTrue({"elo", "casa", "ataque"} <= set(weights))


if __name__ == "__main__":
    unittest.main()
