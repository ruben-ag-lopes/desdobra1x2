"""Run with: python -m unittest tests.test_conferencia"""

import unittest
from datetime import date

from app.models import PrizeTier, UltimoSorteio
from app.services import conferencia


def _tier(nome: str) -> PrizeTier:
    return PrizeTier(nome=nome, vencedores_total=0, valor="€ 1,00")


TOTOLOTO = UltimoSorteio(
    game="totoloto",
    concurso="084/2026",
    data_sorteio=date(2026, 10, 21),
    chave=[1, 4, 12, 18, 26],
    chave_extra=[8],
    ordem_saida=[26, 18, 12, 1, 4, 8],
    premios=[
        _tier("1.º Prémio — 5 Números + Nº da Sorte"),
        _tier("2.º Prémio — 5 Números"),
        _tier("3.º Prémio — 4 Números + Nº da Sorte"),
        _tier("4.º Prémio — 4 Números"),
        _tier("5.º Prémio — 3 Números + Nº da Sorte"),
        _tier("6.º Prémio — 3 Números"),
    ],
)

EUROMILHOES = UltimoSorteio(
    game="euromilhoes",
    concurso="040/2026",
    data_sorteio=date(2026, 10, 20),
    chave=[3, 10, 22, 35, 49],
    chave_extra=[2, 9],
    ordem_saida=[3, 10, 22, 35, 49, 2, 9],
    premios=[
        _tier("1.º Prémio — 5 Números + 2 Estrelas"),
        _tier("2.º Prémio — 5 Números + 1 Estrela"),
        _tier("3.º Prémio — 5 Números + 0 Estrelas"),
        _tier("4.º Prémio — 4 Números + 2 Estrelas"),
        _tier("5.º Prémio — 4 Números + 1 Estrela"),
        _tier("6.º Prémio — 4 Números + 0 Estrelas"),
    ],
)


class ParseApostaTest(unittest.TestCase):
    def test_plus_separates_extra(self):
        self.assertEqual(conferencia.parse_aposta("totoloto", "3 4 6 7 8 + 1"), ([3, 4, 6, 7, 8], [1]))

    def test_without_plus_last_numbers_are_extra(self):
        self.assertEqual(conferencia.parse_aposta("euromilhoes", "1 2 3 4 5 6 7"), ([1, 2, 3, 4, 5], [6, 7]))

    def test_wrong_count_is_rejected(self):
        with self.assertRaises(ValueError):
            conferencia.parse_aposta("totoloto", "3 4 6 7 + 1")

    def test_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            conferencia.parse_aposta("totoloto", "3 4 6 7 50 + 1")

    def test_repeated_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            conferencia.parse_aposta("totoloto", "3 3 6 7 8 + 1")


class ConferirTest(unittest.TestCase):
    def test_no_prize_when_nothing_matches(self):
        result = conferencia.conferir("totoloto", TOTOLOTO, [2, 3, 5, 6, 7], [2])
        self.assertIsNone(result.premio)
        self.assertTrue(result.tabela_disponivel)
        self.assertEqual(result.acertos, [])

    def test_totoloto_four_numbers_and_lucky_number_wins_third_prize(self):
        result = conferencia.conferir("totoloto", TOTOLOTO, [1, 4, 12, 18, 40], [8])
        self.assertEqual(result.acertos, [1, 4, 12, 18])
        self.assertEqual(result.acertos_extra, [8])
        self.assertEqual(result.premio.nome, "3.º Prémio — 4 Números + Nº da Sorte")

    def test_totoloto_four_numbers_without_lucky_number_wins_fourth_prize(self):
        result = conferencia.conferir("totoloto", TOTOLOTO, [1, 4, 12, 18, 40], [7])
        self.assertEqual(result.premio.nome, "4.º Prémio — 4 Números")

    def test_totoloto_jackpot(self):
        result = conferencia.conferir("totoloto", TOTOLOTO, [26, 18, 12, 4, 1], [8])
        self.assertEqual(result.premio.nome, "1.º Prémio — 5 Números + Nº da Sorte")

    def test_totoloto_five_numbers_without_lucky_number_wins_second_prize(self):
        result = conferencia.conferir("totoloto", TOTOLOTO, [26, 18, 12, 4, 1], [7])
        self.assertEqual(result.premio.nome, "2.º Prémio — 5 Números")

    def test_euromilhoes_stars_must_match_exactly(self):
        # 5 numbers + 1 star is the 2nd tier, not the 1st (which needs both stars).
        result = conferencia.conferir("euromilhoes", EUROMILHOES, [3, 10, 22, 35, 49], [2, 1])
        self.assertEqual(result.premio.nome, "2.º Prémio — 5 Números + 1 Estrela")

    def test_euromilhoes_zero_stars_tier(self):
        result = conferencia.conferir("euromilhoes", EUROMILHOES, [3, 10, 22, 35, 49], [1, 4])
        self.assertEqual(result.premio.nome, "3.º Prémio — 5 Números + 0 Estrelas")

    def test_missing_prize_table_is_reported(self):
        empty = TOTOLOTO.model_copy(update={"premios": []})
        result = conferencia.conferir("totoloto", empty, [1, 4, 12, 18, 26], [8])
        self.assertFalse(result.tabela_disponivel)
        self.assertIsNone(result.premio)


if __name__ == "__main__":
    unittest.main()
