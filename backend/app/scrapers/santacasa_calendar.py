from datetime import date, datetime

import re

import httpx
from bs4 import BeautifulSoup

from app.cache import TTLCache
from app.models import Draw, FixtureInfo

_cache = TTLCache(ttl_seconds=3600)

_URLS = {
    "totobola": "https://www.jogossantacasa.pt/web/JogarTotobola/",
    "totoloto": "https://www.jogossantacasa.pt/web/JogarTotoloto/",
    "euromilhoes": "https://www.jogossantacasa.pt/web/JogarEuromilhoes/",
    "eurodreams": "https://www.jogossantacasa.pt/web/JogarEuroDreams/",
}


def _parse_pt_datetime(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%d/%m/%Y %H:%M:%S")


def _parse_pt_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%d/%m/%Y").date()


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("cp1252", errors="replace")


def _fetch_contest_matches(contest_id: str) -> list[FixtureInfo]:
    resp = httpx.post(
        _URLS["totobola"] + "verDetalhe",
        data={"Contest": f"{contest_id}.0"},
        timeout=15,
        follow_redirects=True,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(_decode(resp.content), "html.parser")

    fixtures: list[FixtureInfo] = []
    for li in soup.select("div.currGame li"):
        ems = [e.get_text(strip=True) for e in li.select("span em")]
        if len(ems) < 2 or "-" not in ems[1]:
            continue
        # Team names may contain hyphens (e.g. "Man. City-Real Madrid"); split on the
        # first " - "-less hyphen that yields two non-empty sides.
        home, _, away = ems[1].partition("-")
        competition = ems[2].strip("() ") if len(ems) > 2 else ""
        fixtures.append(FixtureInfo(home_team=home.strip(), away_team=away.strip(), competition=competition))
    return fixtures


def get_contest_matches(contest_id: str) -> list[FixtureInfo]:
    """Fixtures of a Totobola/Totobola Extra contest, straight from the official site."""
    if not re.fullmatch(r"\d+", contest_id):
        raise ValueError("invalid contest id")
    return _cache.get_or_set(f"totobola_matches:{contest_id}", lambda: _fetch_contest_matches(contest_id))


def _fetch_totobola_draws() -> list[Draw]:
    resp = httpx.get(_URLS["totobola"], timeout=15, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(_decode(resp.content), "html.parser")

    draws: list[Draw] = []
    for block in soup.select("div.tbolaPlayBlock"):
        items = [li.get_text(strip=True) for li in block.select("div.betMiddle ul li")]
        # Expected order: [concurso, deadline, tipo, sorteio_date, preco]
        if len(items) < 4:
            continue
        concurso, deadline, tipo, sorteio = items[0], items[1], items[2], items[3]
        form = block.select_one("form input[name=Contest]")
        contest_id = form["value"].split(".")[0] if form and form.get("value") else None
        game = "totobola_extra" if "extra" in tipo.lower() else "totobola"
        try:
            draws.append(
                Draw(
                    game=game,
                    concurso=concurso,
                    contest_id=contest_id,
                    fecha_apostas=_parse_pt_datetime(deadline),
                    data_sorteio=_parse_pt_date(sorteio),
                )
            )
        except ValueError:
            continue
    return draws


def get_totobola_draws() -> list[Draw]:
    """Active Totobola / Totobola Extra concursos with deadlines and draw dates.

    Fixtures per concurso come from get_contest_matches().
    """
    return _cache.get_or_set("totobola_draws", _fetch_totobola_draws)


_NEXT_DRAW_TITLE = re.compile(r"sorteio\s+(\d+/\d{4})", re.IGNORECASE)
_NEXT_DRAW_DATE = re.compile(r"(\d{2}/\d{2}/\d{4}).*?(\d{1,2})h(\d{2})?", re.IGNORECASE)


def _fetch_lottery_draw(game: str) -> Draw | None:
    """Next draw of Totoloto / Euromilhões / EuroDreams, from the banner on the game page."""
    resp = httpx.get(_URLS[game], timeout=15, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(_decode(resp.content), "html.parser")

    title = soup.select_one(".nextDraw .title")
    date_el = soup.select_one(".nextDraw .date")
    if not title or not date_el:
        return None
    m_title = _NEXT_DRAW_TITLE.search(title.get_text(" ", strip=True))
    m_date = _NEXT_DRAW_DATE.search(date_el.get_text(" ", strip=True))
    if not m_title or not m_date:
        return None

    day = _parse_pt_date(m_date.group(1))
    deadline = datetime(day.year, day.month, day.day, int(m_date.group(2)), int(m_date.group(3) or 0))
    return Draw(game=game, concurso=m_title.group(1), fecha_apostas=deadline, data_sorteio=day)


def get_lottery_draw(game: str) -> Draw | None:
    if game not in ("totoloto", "euromilhoes", "eurodreams"):
        raise ValueError(f"unknown lottery game: {game}")
    return _cache.get_or_set(f"{game}_draw", lambda: _fetch_lottery_draw(game))


def get_active_draws() -> list[Draw]:
    return get_totobola_draws()
