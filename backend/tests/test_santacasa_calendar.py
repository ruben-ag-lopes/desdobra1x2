"""Run with: python -m unittest tests.test_santacasa_calendar

Regression tests for the 2026-10 Santa Casa site redesign, which removed the old
div.tbolaPlayBlock/verDetalhe lookup (see app/scrapers/santacasa_calendar.py).
"""

import unittest
from unittest.mock import patch

from app.scrapers import santacasa_calendar as sc

_JOGAR_TOTOBOLA_HTML = """
<em class="nextDraw">
  <span class="title">Concurso Nº41/2026</span>
  <span class="date">Sábado dia 10/10/2026, em jogo até às 14h00</span>
</em>
<em class="nextDraw"><span class="title">Próximo sorteio quinta-feira</span></em>
<div class="currGame">
  <ul><li><strong>1</strong>SL Benfica-V. Guimarães<span><em>Jogo nº1</em><em>SL Benfica-V. Guimarães</em><em>(Primeira Liga)</em></span></li></ul>
</div>
<div class="currGame">
  <ul><li><strong>2</strong>Marítimo-FC Porto<span><em>Jogo nº2</em><em>Marítimo-FC Porto</em><em>(Primeira Liga)</em></span></li></ul>
</div>
<div class="currGame"><ul></ul></div>
"""


class TotobolaDrawsTest(unittest.TestCase):
    def test_parses_the_single_active_contest_into_both_games(self):
        with patch("httpx.get") as get:
            get.return_value.content = _JOGAR_TOTOBOLA_HTML.encode()
            get.return_value.raise_for_status = lambda: None
            draws = sc._fetch_totobola_draws()

        self.assertEqual({d.game for d in draws}, {"totobola", "totobola_extra"})
        for d in draws:
            self.assertEqual(d.concurso, "41/2026")
            self.assertEqual(str(d.fecha_apostas), "2026-10-10 14:00:00")
            self.assertEqual(str(d.data_sorteio), "2026-10-11")  # draws the day after betting closes
            self.assertEqual(d.contest_id, "412026")

    def test_fixtures_come_from_the_front_page_directly(self):
        with patch("httpx.get") as get:
            get.return_value.content = _JOGAR_TOTOBOLA_HTML.encode()
            get.return_value.raise_for_status = lambda: None
            fixtures = sc._fetch_contest_matches()

        self.assertEqual(len(fixtures), 2)
        self.assertEqual(fixtures[0].home_team, "SL Benfica")
        self.assertEqual(fixtures[0].away_team, "V. Guimarães")
        self.assertEqual(fixtures[0].competition, "Primeira Liga")

    def test_missing_banner_returns_no_draws(self):
        with patch("httpx.get") as get:
            get.return_value.content = b"<p>empty</p>"
            get.return_value.raise_for_status = lambda: None
            self.assertEqual(sc._fetch_totobola_draws(), [])
