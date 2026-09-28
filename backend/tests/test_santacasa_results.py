"""Run with: python -m unittest tests.test_santacasa_results

Parses small HTML fixtures mirroring the real page structure (docs/plano-numeros-frequentes.md),
so the parser is tested without hitting the network. The "colums"/"columns" class-name mismatch
between Santa Casa's two page templates is intentional in the fixtures below.
"""

import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from app.scrapers import santacasa_results as sr

_RESULT_HTML = """
<span class="dataInfo">Sorteio: 077/2026 - sábado<br>Data do Sorteio - 26/09/2026</span>
<select name="selectContest">
  <option value="15096.0">077/2026 - sábado</option>
  <option value="15084.0">065/2026 - sábado</option>
</select>
<div class="betMiddle twocol regPad">
  <ul class="colums">
    <li>12 13 17 38 45 + 11</li>
    <li>38 45 12 13 17 + 11</li>
  </ul>
</div>
<div class="stripped betMiddle fourcol regPad">
  <ul class="colums"><li>1.º Prémio</li><li>5 Números + Nº da Sorte</li><li>0</li><li>(1)</li></ul>
  <ul class="colums"><li>3.º Prémio</li><li>4 Números</li><li>143</li><li>€ 347,68</li></ul>
</div>
<div class="stripped betMiddle customfiveCol regPad">
  <ul class="colums"><li>1.º Prémio</li><li>5 Números + 2 Estrelas</li><li class="litleCol">0</li><li class="litleCol">1</li><li>€ 130.000.000,00</li></ul>
</div>
"""


def _fixture(concurso: str, data: str, chave: str) -> str:
    return f"""
    <span class="dataInfo">Sorteio: {concurso}<br>Data do Sorteio - {data}</span>
    <div class="betMiddle twocol regPad">
      <ul class="columns"><li>{chave}</li><li>{chave}</li></ul>
    </div>
    """


class UltimoSorteioTest(unittest.TestCase):
    def _patched(self):
        return patch.object(sr, "_soup", return_value=BeautifulSoup(_RESULT_HTML, "html.parser"))

    def test_parses_key_and_prizes(self):
        with self._patched():
            result = sr._fetch_ultimo_sorteio("totoloto")
        self.assertEqual(result.concurso, "077/2026 - sábado")
        self.assertEqual(str(result.data_sorteio), "2026-09-26")
        self.assertEqual(result.chave, [12, 13, 17, 38, 45])
        self.assertEqual(result.chave_extra, [11])
        self.assertEqual(result.ordem_saida, [38, 45, 12, 13, 17, 11])

    def test_prize_tiers_from_both_tables(self):
        with self._patched():
            result = sr._fetch_ultimo_sorteio("totoloto")
        self.assertEqual(len(result.premios), 3)
        self.assertEqual(result.premios[1].vencedores_total, 143)
        self.assertEqual(result.premios[1].valor, "€ 347,68")

    def test_two_column_prize_row_splits_portugal_and_total(self):
        with self._patched():
            result = sr._fetch_ultimo_sorteio("euromilhoes")
        jackpot = result.premios[-1]
        self.assertEqual(jackpot.vencedores_portugal, 0)
        self.assertEqual(jackpot.vencedores_total, 1)


class FrequenciaTest(unittest.TestCase):
    """_fetch_frequencia fetches the front page once, then one page per listed contest id."""

    def test_counts_numbers_across_the_recent_draws_only(self):
        pages = {
            "front": _fixture("003/2026", "15/01/2026", "1 2 3 4 5 + 9"),
            "b.0": _fixture("002/2026", "12/01/2026", "1 2 3 4 6 + 9"),
            "c.0": _fixture("001/2026", "08/01/2026", "1 2 3 4 7 + 9"),
        }
        front = BeautifulSoup(
            pages["front"] + '<select name="selectContest">'
            '<option value="a.0">003/2026</option><option value="b.0">002/2026</option>'
            '<option value="c.0">001/2026</option></select>',
            "html.parser",
        )

        def fake_soup(url: str) -> BeautifulSoup:
            key = "b.0" if "b.0" in url else "c.0" if "c.0" in url else "front"
            return BeautifulSoup(pages[key], "html.parser") if key != "front" else front

        with patch.object(sr, "_soup", side_effect=fake_soup), patch.object(sr, "_MAX_NUMBER", {"totoloto": 9}):
            result = sr._fetch_frequencia("totoloto")

        self.assertEqual(result.n_sorteios, 3)
        self.assertEqual(str(result.desde), "2026-01-08")  # oldest of the 3 draws
        by_number = {n.numero: n for n in result.numeros}
        self.assertEqual(by_number[1].saidas, 3)  # in every draw
        self.assertEqual(by_number[1].ausencias, 0)  # came out in the newest draw
        self.assertEqual(by_number[5].saidas, 1)  # only the newest draw
        self.assertEqual(by_number[7].saidas, 1)  # only the oldest draw
        self.assertEqual(by_number[7].ausencias, 2)  # 2 more recent draws without it
        self.assertEqual(by_number[8].saidas, 0)  # never drawn
        self.assertEqual(by_number[8].ausencias, 3)
        self.assertIsNone(by_number[8].ultimo_sorteio)
        self.assertAlmostEqual(by_number[1].percentagem, 100.0)
        self.assertAlmostEqual(by_number[5].percentagem, 100 / 3, places=1)

    def test_no_dropdown_raises(self):
        with patch.object(sr, "_soup", return_value=BeautifulSoup("<p>empty</p>", "html.parser")):
            with self.assertRaises(ValueError):
                sr._fetch_frequencia("totoloto")
