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

_STATS_HTML = """
<span class="dataInfo">Dados atualizados em: 27/09/2026 03:00<br>Informação disponível desde: 13/03/2011</span>
<div class="stripped betMiddle sixcol">
  <ul class="colums"><li>1</li><li>137</li><li>8,45</li><li>076/2026</li><li>23/09/2026</li><li>1</li></ul>
  <ul class="colums"><li>2</li><li>162</li><li>9,99</li><li>075/2026</li><li>19/09/2026</li><li>2</li></ul>
</div>
<div class="stripped betMiddle sixcol">
  <ul class="columns"><li>1</li><li>500</li><li>25,0</li><li>077/2026</li><li>26/09/2026</li><li>0</li></ul>
</div>
"""


def _patched(html: str):
    return patch.object(sr, "_soup", return_value=BeautifulSoup(html, "html.parser"))


class UltimoSorteioTest(unittest.TestCase):
    def test_parses_key_and_prizes(self):
        with _patched(_RESULT_HTML):
            result = sr._fetch_ultimo_sorteio("totoloto")
        self.assertEqual(result.concurso, "077/2026 - sábado")
        self.assertEqual(str(result.data_sorteio), "2026-09-26")
        self.assertEqual(result.chave, [12, 13, 17, 38, 45])
        self.assertEqual(result.chave_extra, [11])
        self.assertEqual(result.ordem_saida, [38, 45, 12, 13, 17, 11])

    def test_prize_tiers_from_both_tables(self):
        with _patched(_RESULT_HTML):
            result = sr._fetch_ultimo_sorteio("totoloto")
        self.assertEqual(len(result.premios), 3)
        self.assertEqual(result.premios[1].vencedores_total, 143)
        self.assertEqual(result.premios[1].valor, "€ 347,68")

    def test_two_column_prize_row_splits_portugal_and_total(self):
        with _patched(_RESULT_HTML):
            result = sr._fetch_ultimo_sorteio("euromilhoes")
        jackpot = result.premios[-1]
        self.assertEqual(jackpot.vencedores_portugal, 0)
        self.assertEqual(jackpot.vencedores_total, 1)


class FrequenciaTest(unittest.TestCase):
    def test_only_the_first_table_is_used(self):
        # Regression: the bonus-number table (e.g. "Número da Sorte") must not be mixed in.
        with _patched(_STATS_HTML):
            result = sr._fetch_frequencia("totoloto")
        self.assertEqual(str(result.desde), "2011-03-13")
        self.assertEqual([n.numero for n in result.numeros], [1, 2])
        self.assertEqual(result.numeros[0].saidas, 137)
        self.assertEqual(result.numeros[0].percentagem, 8.45)
        self.assertEqual(result.numeros[0].ausencias, 1)

    def test_columns_class_spelling_is_also_recognised(self):
        # EuroDreams' template spells the class "columns", not "colums" like the others.
        html = _STATS_HTML.replace('<div class="stripped betMiddle sixcol">\n  <ul class="colums">', "PLACEHOLDER")
        only_columns_spelling = _STATS_HTML.split('<div class="stripped betMiddle sixcol">')[0] + (
            '<div class="stripped betMiddle sixcol">\n  <ul class="columns"><li>9</li><li>9</li><li>9,0</li>'
            "<li>077/2026</li><li>26/09/2026</li><li>0</li></ul>\n</div>"
        )
        with _patched(only_columns_spelling):
            result = sr._fetch_frequencia("eurodreams")
        self.assertEqual([n.numero for n in result.numeros], [9])
