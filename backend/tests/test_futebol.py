"""Run with: python -m unittest tests.test_futebol"""

import unittest
from datetime import datetime

from app.research.data import Fixture
from app.services.futebol import _matches_query, _no_margin


def _fixture(home: str, away: str, league: str = "P1") -> Fixture:
    return Fixture(league, datetime(2026, 10, 3, 20, 30), home, away, None, None)


class SearchTest(unittest.TestCase):
    def test_accents_case_and_club_prefixes_do_not_matter(self):
        game = _fixture("Benfica", "Porto")
        for query in ("benfica", "Benfica", "SL Benfica", "benfíca", "benfica porto", "FC Porto"):
            self.assertTrue(_matches_query(game, query), query)
        self.assertFalse(_matches_query(game, "sporting"))

    def test_portuguese_names_find_the_dataset_name(self):
        self.assertTrue(_matches_query(_fixture("Sp Lisbon", "Sp Braga"), "Sporting Braga"))
        self.assertTrue(_matches_query(_fixture("Bayern Munich", "Dortmund", "D1"), "bayern munique"))

    def test_competition_name_matches_its_games(self):
        self.assertTrue(_matches_query(_fixture("Benfica", "Porto"), "primeira liga"))


class BookmakerTest(unittest.TestCase):
    def test_margin_is_removed(self):
        probs = _no_margin((2.0, 3.4, 3.8))
        self.assertAlmostEqual(sum(probs), 1.0)
        self.assertGreater(probs[0], probs[1])
        self.assertIsNone(_no_margin(None))
