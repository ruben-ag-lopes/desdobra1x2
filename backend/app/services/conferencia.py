"""Checks a bet against the winning key and prize table of a game's last draw.

The prize table is the one the Santa Casa publishes (see santacasa_results): each tier is named
like "1.º Prémio — 5 Números + 2 Estrelas" or "3.º Prémio — 4 Números". We read the hit counts
straight from those names, so the rules are whatever the site says, not a copy of them here.
"""

import re

from app.models import ConferirResponse, UltimoSorteio
from app.services.lottery_generator import RULES

_NUMBER = re.compile(r"\d+")
_MAIN_HITS = re.compile(r"(\d+)\s+N\w*mero", re.IGNORECASE)  # "5 Números", "1 Número"
_STARS = re.compile(r"(\d+)\s+Estrelas?", re.IGNORECASE)  # Euromilhões: "2 Estrelas", "0 Estrelas"


def parse_aposta(game: str, texto: str) -> tuple[list[int], list[int]]:
    """Split "3 4 6 7 8 + 1" into main and extra numbers. Without the "+", the last numbers are the extra."""
    rules = RULES[game]
    if "+" in texto:
        principal, _, extra = texto.partition("+")
        numbers, extra_numbers = _NUMBER.findall(principal), _NUMBER.findall(extra)
    else:
        todos = _NUMBER.findall(texto)
        numbers, extra_numbers = todos[: -rules["extra_count"]], todos[-rules["extra_count"] :]
    numbers, extra_numbers = [int(n) for n in numbers], [int(n) for n in extra_numbers]

    if len(numbers) != rules["main_count"] or len(extra_numbers) != rules["extra_count"]:
        raise ValueError(
            f"Uma aposta de {game} tem {rules['main_count']} números + {rules['extra_count']} extra "
            "(ex.: 3 4 6 7 8 + 1)."
        )
    main_lo, main_hi = rules["main_range"]
    extra_lo, extra_hi = rules["extra_range"]
    if any(not main_lo <= n <= main_hi for n in numbers) or len(set(numbers)) != len(numbers):
        raise ValueError(f"Os números têm de ser entre {main_lo} e {main_hi}, sem repetir.")
    if any(not extra_lo <= n <= extra_hi for n in extra_numbers) or len(set(extra_numbers)) != len(extra_numbers):
        raise ValueError(f"O extra tem de ser entre {extra_lo} e {extra_hi}, sem repetir.")
    return numbers, extra_numbers


def _tier_hits(nome: str) -> tuple[int, int | None] | None:
    """(main hits, extra hits) a prize tier needs. None for the extra means it doesn't depend on it."""
    main = _MAIN_HITS.search(nome)
    if main is None:
        return None
    stars = _STARS.search(nome)
    if stars:
        return int(main.group(1)), int(stars.group(1))
    if re.search(r"Sorte|Dream", nome, re.IGNORECASE):  # Totoloto's "Nº da Sorte", EuroDreams' dream number
        return int(main.group(1)), 1
    return int(main.group(1)), None


def conferir(game: str, sorteio: UltimoSorteio, numeros: list[int], numeros_extra: list[int]) -> ConferirResponse:
    acertos = sorted(set(numeros) & set(sorteio.chave))
    acertos_extra = sorted(set(numeros_extra) & set(sorteio.chave_extra))

    premio = None
    # The table lists the best tiers first, so the first match is the prize the bet wins.
    for tier in sorteio.premios:
        hits = _tier_hits(tier.nome)
        if hits is None:
            continue
        main_needed, extra_needed = hits
        if len(acertos) == main_needed and (extra_needed is None or len(acertos_extra) == extra_needed):
            premio = tier
            break

    return ConferirResponse(
        concurso=sorteio.concurso,
        data_sorteio=sorteio.data_sorteio,
        tabela_disponivel=bool(sorteio.premios),
        numeros=numeros,
        numeros_extra=numeros_extra,
        acertos=acertos,
        acertos_extra=acertos_extra,
        premio=premio,
    )
