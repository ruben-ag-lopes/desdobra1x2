"""Run with: python -m unittest tests.test_santacasa_calendar

The JogarTotobola page has two layouts, depending on how many contests are open:
- several open (Totobola + Totobola Extra): a list of div.tbolaPlayBlock, one per contest, each with a
  'Jogar' form carrying its Contest id; the games come from a POST to .../verDetalhe;
- only one open: the list is skipped and a 'Concurso Nº.../em jogo até' banner plus the games are
  shown directly on the page.
Both were observed live (2026-10-06 single view, 2026-10-08 list view); each broke a scraper that
only knew the other.
"""

import unittest
from unittest.mock import patch

from app.scrapers import santacasa_calendar as sc

_LIST_VIEW_HTML = """
<div class="bgCenter sendBtn betnow">
  <strong class="totobola">Totobola</strong>
  <div class="tbolaPlayBlock">
    <div class="betMiddle fivecol"><ul>
      <li><span>41/2026</span></li><li><span>10/10/2026  14:00:00</span></li>
      <li><span>Totobola</span></li><li><span>11/10/2026</span></li><li><span>€0,50</span></li>
    </ul></div>
    <form action="/web/JogarTotobola/verDetalhe" method="post"><input name="Contest" type="hidden" value="15217.0"/></form>
  </div>
  <div class="tbolaPlayBlock">
    <div class="betMiddle fivecol"><ul>
      <li><span>41/2026</span></li><li><span>13/10/2026  16:45:00</span></li>
      <li><span>Totobola Extra</span></li><li><span>15/10/2026</span></li><li><span>€0,50</span></li>
    </ul></div>
    <form action="/web/JogarTotobola/verDetalhe" method="post"><input name="Contest" type="hidden" value="15272.0"/></form>
  </div>
</div>
"""

_SINGLE_VIEW_HTML = """
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


def _response(html: str):
    class R:
        content = html.encode()

        def raise_for_status(self):
            pass

    return R()


class TotobolaDrawsTest(unittest.TestCase):
    def test_list_view_gives_separate_totobola_and_extra_contests(self):
        with patch("httpx.get", return_value=_response(_LIST_VIEW_HTML)):
            draws = {d.game: d for d in sc._fetch_totobola_draws()}

        self.assertEqual(set(draws), {"totobola", "totobola_extra"})
        self.assertEqual(draws["totobola"].contest_id, "15217")
        self.assertEqual(draws["totobola_extra"].contest_id, "15272")
        self.assertEqual(str(draws["totobola"].fecha_apostas), "2026-10-10 14:00:00")
        self.assertEqual(str(draws["totobola_extra"].fecha_apostas), "2026-10-13 16:45:00")
        self.assertEqual(str(draws["totobola_extra"].data_sorteio), "2026-10-15")  # published, not estimated

    def test_single_view_gives_only_the_one_open_contest(self):
        with patch("httpx.get", return_value=_response(_SINGLE_VIEW_HTML)):
            draws = sc._fetch_totobola_draws()

        self.assertEqual([d.game for d in draws], ["totobola"])
        self.assertEqual(draws[0].concurso, "41/2026")
        self.assertEqual(draws[0].contest_id, "inline")
        self.assertEqual(str(draws[0].fecha_apostas), "2026-10-10 14:00:00")
        self.assertEqual(str(draws[0].data_sorteio), "2026-10-11")  # no date published: the day after the deadline

    def test_a_page_with_no_contest_returns_nothing(self):
        with patch("httpx.get", return_value=_response("<p>empty</p>")):
            self.assertEqual(sc._fetch_totobola_draws(), [])


class ContestMatchesTest(unittest.TestCase):
    def test_inline_contest_reads_the_games_from_the_front_page(self):
        with patch("httpx.get", return_value=_response(_SINGLE_VIEW_HTML)) as get:
            fixtures = sc._fetch_contest_matches("inline")

        get.assert_called_once()
        self.assertEqual(len(fixtures), 2)
        self.assertEqual(fixtures[0].home_team, "SL Benfica")
        self.assertEqual(fixtures[0].away_team, "V. Guimarães")
        self.assertEqual(fixtures[0].competition, "Primeira Liga")

    def test_listed_contest_posts_its_id_to_verdetalhe(self):
        with patch("httpx.post", return_value=_response(_SINGLE_VIEW_HTML)) as post:
            fixtures = sc._fetch_contest_matches("15272")

        self.assertEqual(post.call_args.kwargs["data"], {"Contest": "15272.0"})
        self.assertTrue(post.call_args.args[0].endswith("/verDetalhe"))
        self.assertEqual(len(fixtures), 2)

    def test_rejects_ids_that_are_neither_digits_nor_the_inline_sentinel(self):
        for bad in ("../x", "41/2026", "15272.0", ""):
            with self.assertRaises(ValueError):
                sc.get_contest_matches(bad)


class EmptyResultsAreNotCachedTest(unittest.TestCase):
    def test_an_empty_answer_is_retried_instead_of_pinned_for_an_hour(self):
        sc._cache._store.clear()
        with patch("httpx.get", return_value=_response("<p>empty</p>")) as get:
            self.assertEqual(sc.get_totobola_draws(), [])
            self.assertEqual(sc.get_totobola_draws(), [])
        self.assertEqual(get.call_count, 2)  # fetched both times: nothing was cached
        sc._cache._store.clear()
