"""Run with: python -m unittest tests.test_bilhete"""

import unittest
from datetime import date

from app.models import BilhetePremio, UltimoBilhete
from app.services import bilhete

CLASSICA = UltimoBilhete(
    game="lotaria_classica",
    concurso="043/2026",
    data_sorteio=date(2026, 10, 27),
    premios=[
        BilhetePremio(nome="1.º Prémio", bilhete="10138", valores=["€ 600.000,00", "€ 60.000,00"]),
        BilhetePremio(nome="2.º Prémio", bilhete="57468", valores=["€ 60.000,00", "€ 6.000,00"]),
    ],
    sequencias_digitos=4,
    sequencias=["5200", "8617"],
)


class ParseBilheteTest(unittest.TestCase):
    def test_accepts_five_digits(self):
        self.assertEqual(bilhete.parse_bilhete(" 10138 "), "10138")

    def test_rejects_other_lengths_and_letters(self):
        for texto in ["1013", "101380", "10a38", ""]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                bilhete.parse_bilhete(texto)


class ConferirBilheteTest(unittest.TestCase):
    def test_exact_prize(self):
        result = bilhete.conferir_bilhete(CLASSICA, "57468")
        self.assertEqual(result.premio.nome, "2.º Prémio")
        self.assertIsNone(result.sequencia)

    def test_sequence_on_the_last_digits(self):
        result = bilhete.conferir_bilhete(CLASSICA, "98617")
        self.assertIsNone(result.premio)
        self.assertEqual(result.sequencia, "8617")

    def test_no_prize(self):
        result = bilhete.conferir_bilhete(CLASSICA, "00001")
        self.assertIsNone(result.premio)
        self.assertIsNone(result.sequencia)


class SugerirBilheteTest(unittest.TestCase):
    def test_suggestion_is_five_digits_with_leading_zeros(self):
        for _ in range(200):
            self.assertRegex(bilhete.sugerir_bilhete().bilhete, r"^\d{5}$")


if __name__ == "__main__":
    unittest.main()
