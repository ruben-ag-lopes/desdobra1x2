"""Code games (M1lhão, Chuva de Milionários): check a code against the winning codes, suggest one."""

import random
import re
import string

from app.models import ConferirCodigoResponse, SugestaoCodigoResponse, UltimoCodigo

CODIGO_GAMES = {"m1lhao", "chuva_milionarios"}
_FORMATO = re.compile(r"[A-Z]{3,4}\d{5}")  # e.g. QRX13538, BWPJ29140


def parse_codigo(texto: str) -> str:
    codigo = texto.strip().upper()
    if not _FORMATO.fullmatch(codigo):
        raise ValueError("O código tem 3 ou 4 letras seguidas de 5 algarismos (ex.: QRX13538).")
    return codigo


def conferir_codigo(sorteio: UltimoCodigo, codigo: str) -> ConferirCodigoResponse:
    # shortcut: every winning code pays the first prize tier, both games have one. Upgrade when a game has several code tiers.
    premio = sorteio.premios[0] if codigo in sorteio.codigos else None
    return ConferirCodigoResponse(concurso=sorteio.concurso, data_sorteio=sorteio.data_sorteio, codigo=codigo, premio=premio)


def sugerir_codigo() -> SugestaoCodigoResponse:
    letras = "".join(random.choices(string.ascii_uppercase, k=4))
    return SugestaoCodigoResponse(codigo=f"{letras}{random.randrange(10**5):05d}")
