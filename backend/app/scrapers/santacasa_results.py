"""Last draw (winning key + prize table) and per-number frequency, scraped from the Santa Casa
results pages (plain server-rendered HTML, no JavaScript needed — see
docs/plano-numeros-frequentes.md for the page URLs and structure this relies on).

The frequency is computed by us, over the recent draws the "Consultar Sorteios" dropdown offers
(~30, several months) — not "since the game started". We tried fetching a full year by walking
contest ids backwards, but ids are shared across all Santa Casa games and are NOT evenly spaced
per game (jumps beyond the dropdown's own range land on other games' draws or on gaps), so the
result would be silently wrong. The dropdown's own list is what the site itself vouches for.
"""

import re
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup

from app.cache import TTLCache
from app.models import (
    BilhetePremio,
    FrequenciaResponse,
    NumberFrequency,
    PrizeTier,
    TotobolaResultado,
    UltimoBilhete,
    UltimoCodigo,
    UltimoConcursoTotobola,
    UltimoSorteio,
)

_cache = TTLCache(ttl_seconds=24 * 3600)

_RESULT_URLS = {
    "totoloto": "https://www.jogossantacasa.pt/web/SCCartazResult/totolotoNew",
    "euromilhoes": "https://www.jogossantacasa.pt/web/SCCartazResult/",
    "eurodreams": "https://www.jogossantacasa.pt/web/ResultsBoard/EuroDreams",
}
_TOTOBOLA_RESULT_URLS = {
    "totobola": "https://www.jogossantacasa.pt/web/SCCartazResult/bolaNormal",
    "totobola_extra": "https://www.jogossantacasa.pt/web/SCCartazResult/bolaExtra1",
}
_BILHETE_URLS = {
    "lotaria_classica": "https://www.jogossantacasa.pt/web/SCCartazResult/lotClass",
    "lotaria_popular": "https://www.jogossantacasa.pt/web/SCCartazResult/lotPop",
}
_CODIGO_URLS = {
    "m1lhao": "https://www.jogossantacasa.pt/web/SCCartazResult/m1lhao",
    "chuva_milionarios": "https://www.jogossantacasa.pt/web/SCCartazResult/cmil",
}
# Highest possible main number, so numbers absent from the sample still show up (0 saídas).
_MAX_NUMBER = {"totoloto": 49, "euromilhoes": 50, "eurodreams": 40}


def _soup(url: str) -> BeautifulSoup:
    resp = httpx.get(url, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _int(text: str) -> int:
    return int(text.replace(".", "").strip() or 0)


def _draw_info(soup: BeautifulSoup) -> tuple[str, date]:
    info = soup.select_one("span.dataInfo")
    if info is None:
        raise ValueError("Could not find the draw info block")
    lines = [line.strip() for line in info.get_text("\n").splitlines() if line.strip()]
    concurso = lines[0].split(":", 1)[1].strip()
    data_sorteio = datetime.strptime(lines[1].rsplit("-", 1)[1].strip(), "%d/%m/%Y").date()
    return concurso, data_sorteio


def _winning_key(soup: BeautifulSoup) -> tuple[list[int], list[int], list[int]]:
    """(chave, chave_extra, ordem_saida) — ordem_saida includes any extra numbers too."""
    key_rows = soup.select("div.betMiddle.twocol.regPad ul[class*='colum'] > li")
    if len(key_rows) < 2:
        raise ValueError("Could not find the winning key")
    main_text, _, extra_text = key_rows[0].get_text(strip=True).partition("+")
    chave = [int(n) for n in main_text.split()]
    chave_extra = [int(n) for n in extra_text.split()] if extra_text else []
    ordem_text, _, ordem_extra_text = key_rows[1].get_text(strip=True).partition("+")
    ordem_saida = [int(n) for n in ordem_text.split()] + ([int(n) for n in ordem_extra_text.split()] if ordem_extra_text else [])
    return chave, chave_extra, ordem_saida


def _recent_contests(soup: BeautifulSoup) -> list[str]:
    """Contest ids the page's own "Consultar Sorteios" dropdown offers, newest first."""
    select = soup.select_one("select[name=selectContest]")
    if select is None:
        return []
    return [opt["value"] for opt in select.select("option") if opt.get("value")]


def _prize_tiers(soup: BeautifulSoup) -> list[PrizeTier]:
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
                valor=re.sub(r"\s+", " ", valor.replace("\xa0", " ")).strip(),
            )
        )
    return premios


def _fetch_ultimo_sorteio(game: str) -> UltimoSorteio:
    soup = _soup(_RESULT_URLS[game])
    concurso, data_sorteio = _draw_info(soup)
    chave, chave_extra, ordem_saida = _winning_key(soup)

    return UltimoSorteio(
        game=game,
        concurso=concurso,
        data_sorteio=data_sorteio,
        chave=chave,
        chave_extra=chave_extra,
        ordem_saida=ordem_saida,
        premios=_prize_tiers(soup),
    )


def _fetch_ultimo_concurso_totobola(game: str) -> UltimoConcursoTotobola:
    soup = _soup(_TOTOBOLA_RESULT_URLS[game])
    concurso, data_concurso = _draw_info(soup)

    resultados = []
    for group in soup.select("div.keyMiddle.left > ul"):
        cells = [li.get_text(strip=True) for li in group.select("li")]
        if len(cells) != 2 or cells[1] not in ("1", "X", "2"):
            continue
        numero, _, jogo = cells[0].partition(".")
        resultados.append(TotobolaResultado(numero=numero.strip(), jogo=jogo.strip(), resultado=cells[1]))
    if not resultados:
        raise ValueError(f"Could not find the match results for {game}")

    return UltimoConcursoTotobola(
        game=game, concurso=concurso, data_concurso=data_concurso, resultados=resultados, premios=_prize_tiers(soup)
    )


def _fetch_ultimo_bilhete(game: str) -> UltimoBilhete:
    soup = _soup(_BILHETE_URLS[game])
    concurso, data_sorteio = _draw_info(soup)

    premios = []
    for row in soup.select("div.stripped.betMiddle ul[class*='colum']"):
        cells = [li.get_text(strip=True) for li in row.select("li")]
        if len(cells) == 4:
            premios.append(BilhetePremio(nome=cells[0], bilhete=cells[1], valores=cells[2:]))
    if not premios:
        raise ValueError(f"Could not find the ticket prizes for {game}")

    # The sequences block sits under a header like "Sequências de 4 algarismos".
    header = next((d for d in soup.select("div.betHeader") if re.search(r"de \d+ algarismos", d.get_text(" "))), None)
    if header is None:
        raise ValueError(f"Could not find the sequences for {game}")
    digitos = int(re.search(r"de (\d+)", header.get_text(" ")).group(1))
    body = header.find_next_sibling("div", class_="betMiddle")
    sequencias = re.findall(r"\d+", body.get_text(" ")) if body else []

    nome_sorteio = soup.select_one("span.totalBet strong").get_text(strip=True)
    return UltimoBilhete(
        game=game, nome_sorteio=nome_sorteio, concurso=concurso, data_sorteio=data_sorteio, premios=premios, sequencias_digitos=digitos, sequencias=sequencias
    )


def _fetch_ultimo_codigo(game: str) -> UltimoCodigo:
    soup = _soup(_CODIGO_URLS[game])
    concurso, data_sorteio = _draw_info(soup)

    codigos = [li.get_text(strip=True) for li in soup.select("li[id^='code_']")]
    if not codigos:
        raise ValueError(f"Could not find the winning codes for {game}")

    premios = []
    for row in soup.select("div.stripped ul[class*='colum']"):
        cells = [re.sub(r"\s+", " ", li.get_text(" ")).strip() for li in row.select("li")]
        if len(cells) not in (3, 4):
            continue
        # With 4 cells the table splits Portugal from the total: nome, PT, total, valor.
        nome, *vencedores, valor = cells
        pt, total = (_int(vencedores[0]), _int(vencedores[1])) if len(vencedores) == 2 else (None, _int(vencedores[0]))
        premios.append(PrizeTier(nome=nome, vencedores_portugal=pt, vencedores_total=total, valor=valor))

    return UltimoCodigo(game=game, concurso=concurso, data_sorteio=data_sorteio, codigos=codigos, premios=premios)


def _fetch_frequencia(game: str) -> FrequenciaResponse:
    """Number frequency over the recent draws the site's own dropdown lists (see module docstring)."""
    front_page = _soup(_RESULT_URLS[game])
    contest_ids = _recent_contests(front_page)
    if not contest_ids:
        raise ValueError(f"Could not find the list of recent draws for {game}")

    draws: list[tuple[str, date, list[int]]] = []
    for i, contest_id in enumerate(contest_ids):
        soup = front_page if i == 0 else _soup(f"{_RESULT_URLS[game]}?selectContest={contest_id}")
        concurso, data_sorteio = _draw_info(soup)
        chave, _, _ = _winning_key(soup)
        draws.append((concurso, data_sorteio, chave))

    last_seen: dict[int, tuple[str, date]] = {}
    counts: dict[int, int] = dict.fromkeys(range(1, _MAX_NUMBER[game] + 1), 0)
    for concurso, data_sorteio, chave in draws:  # newest first: the first hit per number is its latest
        for n in chave:
            counts[n] += 1
            last_seen.setdefault(n, (concurso, data_sorteio))

    total = len(draws)
    numeros = [
        NumberFrequency(
            numero=n,
            saidas=saidas,
            percentagem=round(100 * saidas / total, 2) if total else 0.0,
            ultimo_sorteio=last_seen.get(n, (None, None))[0],
            data_ultimo_sorteio=last_seen.get(n, (None, None))[1],
            ausencias=next((i for i, (_, _, chave) in enumerate(draws) if n in chave), total),
        )
        for n, saidas in counts.items()
    ]

    return FrequenciaResponse(game=game, desde=draws[-1][1], n_sorteios=total, numeros=numeros)


def get_ultimo_sorteio(game: str) -> UltimoSorteio:
    return _cache.get_or_set(f"ultimo_sorteio:{game}", lambda: _fetch_ultimo_sorteio(game))


def get_ultimo_concurso_totobola(game: str) -> UltimoConcursoTotobola:
    return _cache.get_or_set(f"ultimo_concurso_totobola:{game}", lambda: _fetch_ultimo_concurso_totobola(game))


def get_frequencia(game: str) -> FrequenciaResponse:
    return _cache.get_or_set(f"frequencia:{game}", lambda: _fetch_frequencia(game))


def get_ultimo_bilhete(game: str) -> UltimoBilhete:
    return _cache.get_or_set(f"ultimo_bilhete:{game}", lambda: _fetch_ultimo_bilhete(game))


def get_ultimo_codigo(game: str) -> UltimoCodigo:
    return _cache.get_or_set(f"ultimo_codigo:{game}", lambda: _fetch_ultimo_codigo(game))
