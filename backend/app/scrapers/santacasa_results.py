"""Last draw (winning key + prize table) and per-number frequency, scraped from the Santa Casa
results/statistics pages (plain server-rendered HTML, no JavaScript needed — see
docs/plano-numeros-frequentes.md for the page URLs and structure this relies on).

The frequency shown is "since the game started" (what the site itself shows), not a rolling
365-day window: the statistics pages don't offer a date-range filter, only a per-number one. A
365-day figure would need scraping the full draw history separately (see the plan).
"""

from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup, Tag

from app.cache import TTLCache
from app.models import FrequenciaResponse, NumberFrequency, PrizeTier, UltimoSorteio

_cache = TTLCache(ttl_seconds=12 * 3600)

_RESULT_URLS = {
    "totoloto": "https://www.jogossantacasa.pt/web/SCCartazResult/totolotoNew",
    "euromilhoes": "https://www.jogossantacasa.pt/web/SCCartazResult/",
    "eurodreams": "https://www.jogossantacasa.pt/web/ResultsBoard/EuroDreams",
}
_STATS_URLS = {
    "totoloto": "https://www.jogossantacasa.pt/web/SCEstatisticas/totolotoN",
    "euromilhoes": "https://www.jogossantacasa.pt/web/SCEstatisticas/",
    "eurodreams": "https://www.jogossantacasa.pt/web/Statistics/EuroDreams",
}


def _soup(url: str) -> BeautifulSoup:
    resp = httpx.get(url, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _int(text: str) -> int:
    return int(text.replace(".", "").strip() or 0)


def _fetch_ultimo_sorteio(game: str) -> UltimoSorteio:
    soup = _soup(_RESULT_URLS[game])

    info = soup.select_one("span.dataInfo")
    if info is None:
        raise ValueError(f"Could not find the draw info block for {game}")
    lines = [line.strip() for line in info.get_text("\n").splitlines() if line.strip()]
    concurso = lines[0].split(":", 1)[1].strip()
    data_sorteio = datetime.strptime(lines[1].rsplit("-", 1)[1].strip(), "%d/%m/%Y").date()

    key_rows = soup.select("div.betMiddle.twocol.regPad ul[class*='colum'] > li")
    if len(key_rows) < 2:
        raise ValueError(f"Could not find the winning key for {game}")
    main_text, _, extra_text = key_rows[0].get_text(strip=True).partition("+")
    chave = [int(n) for n in main_text.split()]
    chave_extra = [int(n) for n in extra_text.split()] if extra_text else []
    ordem_text, _, ordem_extra_text = key_rows[1].get_text(strip=True).partition("+")
    ordem_saida = [int(n) for n in ordem_text.split()] + ([int(n) for n in ordem_extra_text.split()] if ordem_extra_text else [])

    premios = []
    for row in soup.select("div.stripped.betMiddle ul[class*='colum']"):
        cells = [li.get_text(strip=True) for li in row.select("li")]
        if len(cells) < 4:
            continue
        nome, acertos, *vencedores, valor = cells
        vencedores_total = _int(vencedores[-1]) if vencedores[-1].replace(".", "").isdigit() else 0
        vencedores_portugal = _int(vencedores[0]) if len(vencedores) == 2 and vencedores[0].replace(".", "").isdigit() else None
        premios.append(
            PrizeTier(
                nome=f"{nome} — {acertos}",
                vencedores_portugal=vencedores_portugal,
                vencedores_total=vencedores_total,
                valor=valor.replace("\xa0", " ").strip(),
            )
        )

    return UltimoSorteio(
        game=game,
        concurso=concurso,
        data_sorteio=data_sorteio,
        chave=chave,
        chave_extra=chave_extra,
        ordem_saida=ordem_saida,
        premios=premios,
    )


def _row_cells(row: Tag) -> list[str]:
    return [li.get_text(strip=True) for li in row.select("li")]


def _fetch_frequencia(game: str) -> FrequenciaResponse:
    soup = _soup(_STATS_URLS[game])

    info = soup.select_one("span.dataInfo")
    if info is None:
        raise ValueError(f"Could not find the statistics info block for {game}")
    lines = [line.strip() for line in info.get_text("\n").splitlines() if line.strip()]
    desde_line = next((line for line in lines if "desde" in line.lower()), "")
    desde = datetime.strptime(desde_line.rsplit(":", 1)[-1].strip(), "%d/%m/%Y").date()

    # Some games (Totoloto's "Número da Sorte", EuroDreams's "Nº de Sonho") have a second, smaller
    # number pool with its own sixcol table; the main numbers are always the first one on the page.
    # The row class is spelled "colums" on some pages and "columns" on others.
    tables = soup.select("div.stripped.betMiddle.sixcol")
    if not tables:
        raise ValueError(f"Could not find the frequency table for {game}")
    numeros = []
    for row in tables[0].select("ul[class*='colum']"):
        cells = _row_cells(row)
        if len(cells) != 6:
            continue
        numero, saidas, pct, ultimo, data_txt, ausencias = cells
        numeros.append(
            NumberFrequency(
                numero=int(numero),
                saidas=_int(saidas),
                percentagem=float(pct.replace(",", ".")),
                ultimo_sorteio=ultimo,
                data_ultimo_sorteio=datetime.strptime(data_txt, "%d/%m/%Y").date(),
                ausencias=_int(ausencias),
            )
        )

    return FrequenciaResponse(game=game, desde=desde, numeros=numeros)


def get_ultimo_sorteio(game: str) -> UltimoSorteio:
    return _cache.get_or_set(f"ultimo_sorteio:{game}", lambda: _fetch_ultimo_sorteio(game))


def get_frequencia(game: str) -> FrequenciaResponse:
    return _cache.get_or_set(f"frequencia:{game}", lambda: _fetch_frequencia(game))
