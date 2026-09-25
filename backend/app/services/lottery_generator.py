import random

from app.models import LotteryTicket

# Regras oficiais dos jogos Santa Casa (confirmar periodicamente em jogossantacasa.pt,
# pois a Santa Casa pode alterar os intervalos de números).
RULES = {
    "totoloto": {"main_range": (1, 49), "main_count": 5, "extra_range": (1, 13), "extra_count": 1},
    "euromilhoes": {"main_range": (1, 50), "main_count": 5, "extra_range": (1, 12), "extra_count": 2},
    "eurodreams": {"main_range": (1, 40), "main_count": 6, "extra_range": (1, 5), "extra_count": 1},
}


def generate_ticket(game: str) -> LotteryTicket:
    rules = RULES[game]
    main_lo, main_hi = rules["main_range"]
    extra_lo, extra_hi = rules["extra_range"]

    numbers = sorted(random.sample(range(main_lo, main_hi + 1), rules["main_count"]))
    extra_numbers = sorted(random.sample(range(extra_lo, extra_hi + 1), rules["extra_count"]))

    return LotteryTicket(numbers=numbers, extra_numbers=extra_numbers)


def generate_tickets(game: str, count: int) -> list[LotteryTicket]:
    return [generate_ticket(game) for _ in range(count)]
