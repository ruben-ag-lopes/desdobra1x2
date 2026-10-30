"""Run with: python -m unittest tests.test_codigo"""

import unittest
from datetime import date
from unittest.mock import patch

from bs4 import BeautifulSoup

from app.models import PrizeTier, UltimoCodigo
from app.scrapers import santacasa_results as sr
from app.services import codigo

M1LHAO = UltimoCodigo(
    game="m1lhao",
    concurso="010/2026",
    data_sorteio=date(2026, 10, 30),
    codigos=["QRX13538"],
    premios=[PrizeTier(nome="1.º Prémio", vencedores_total=1, valor="€ 1.000.000,00")],
)

_HTML = """
<span class="dataInfo">Sorteio: 094/2024 - sexta-feira<br>Data do Sorteio - 22/11/2024</span>
<ul><li>1.º Prémio</li><li id='code_cmil'>BWPJ29140</li><li>93</li></ul>
<ul><li>1.º Prémio</li><li id='code_cmil'>BWPP46396</li><li>94</li></ul>
<div class="stripped betMiddle fourcol regPad">
  <ul class="colums"><li>1º Prémio</li><li>9</li><li>100</li><li>€ 1.000.000,00&nbsp;</li></ul>
</div>
"""


class ParseCodigoTest(unittest.TestCase):
    def test_accepts_letters_and_digits(self):
        self.assertEqual(codigo.parse_codigo(" qrx13538 "), "QRX13538")

    def test_rejects_wrong_shape(self):
        for texto in ["QRX1353", "12345678", "QRX135389", ""]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                codigo.parse_codigo(texto)


class ConferirCodigoTest(unittest.TestCase):
    def test_winning_code(self):
        result = codigo.conferir_codigo(M1LHAO, "QRX13538")
        self.assertEqual(result.premio.nome, "1.º Prémio")

    def test_winning_code_without_a_prize_table_does_not_crash(self):
        sem_tabela = M1LHAO.model_copy(update={"premios": []})
        self.assertIsNone(codigo.conferir_codigo(sem_tabela, "QRX13538").premio)

    def test_losing_code(self):
        self.assertIsNone(codigo.conferir_codigo(M1LHAO, "QRX13539").premio)



class FetchUltimoCodigoTest(unittest.TestCase):
    def test_parses_codes_and_prize_with_portugal_split(self):
        with patch.object(sr, "_soup", return_value=BeautifulSoup(_HTML, "html.parser")):
            result = sr._fetch_ultimo_codigo("chuva_milionarios")
        self.assertEqual(result.codigos, ["BWPJ29140", "BWPP46396"])
        self.assertEqual(result.premios[0].vencedores_portugal, 9)
        self.assertEqual(result.premios[0].vencedores_total, 100)
        self.assertEqual(result.premios[0].valor, "€ 1.000.000,00")


if __name__ == "__main__":
    unittest.main()
