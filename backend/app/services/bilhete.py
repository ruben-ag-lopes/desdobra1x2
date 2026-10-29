"""Ticket-number games (Lotaria Clássica, Lotaria Popular): check a ticket and suggest one."""

import random
import re

from app.models import ConferirBilheteResponse, SugestaoBilheteResponse, UltimoBilhete

BILHETE_GAMES = {"lotaria_classica", "lotaria_popular"}
TICKET_DIGITS = 5


def parse_bilhete(texto: str) -> str:
    bilhete = texto.strip()
    if not re.fullmatch(rf"\d{{{TICKET_DIGITS}}}", bilhete):
        raise ValueError(f"O bilhete tem {TICKET_DIGITS} algarismos (ex.: 10138).")
    return bilhete


def conferir_bilhete(sorteio: UltimoBilhete, bilhete: str) -> ConferirBilheteResponse:
    premio = next((p for p in sorteio.premios if p.bilhete == bilhete), None)
    # Sequences pay on the last digits of the ticket, so only the ending matters.
    sequencia = None if premio else next((s for s in sorteio.sequencias if bilhete.endswith(s)), None)
    return ConferirBilheteResponse(
        concurso=sorteio.concurso,
        data_sorteio=sorteio.data_sorteio,
        bilhete=bilhete,
        premio=premio,
        sequencia=sequencia,
    )


def sugerir_bilhete() -> SugestaoBilheteResponse:
    return SugestaoBilheteResponse(bilhete=f"{random.randrange(10**TICKET_DIGITS):0{TICKET_DIGITS}d}")
