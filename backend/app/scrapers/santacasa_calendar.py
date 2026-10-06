from datetime import date, datetime, timedelta

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


def _fetch_contest_matches() -> list[FixtureInfo]:
    """Fixtures of the current Totobola contest. The site used to publish a separate
    'verDetalhe' lookup by contest id; since a 2026-10 redesign the 13 games are listed
    directly on the JogarTotobola page, and there is always exactly one active contest."""
    resp = httpx.get(_URLS["totobola"], timeout=15, follow_redirects=True)
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
    """Fixtures of the current Totobola contest. `contest_id` is only a cache key / URL segment
    now (kept for API compatibility) — the site has no per-contest lookup anymore, see above."""
    if not re.fullmatch(r"\d+", contest_id):
        raise ValueError("invalid contest id")
    return _cache.get_or_set(f"totobola_matches:{contest_id}", _fetch_contest_matches)


_TOTOBOLA_TITLE = re.compile(r"concurso\s*n?º?\s*(\d+/\d{4})", re.IGNORECASE)
_TOTOBOLA_DATE = re.compile(r"(\d{2}/\d{2}/\d{4}).*?(\d{1,2})h(\d{2})?", re.IGNORECASE)


def _fetch_totobola_draws() -> list[Draw]:
    """The active Totobola concurso, from the 'Concurso Nº.../em jogo até às Xh00' banner.

    Totobola and Totobola Extra share the same 13 games and the same deadline — Extra is an
    add-on bet on the same coupon, not a separate contest — so both Draws carry identical data.
    The site no longer publishes a separate draw date; it draws the day after betting closes.
    """
    resp = httpx.get(_URLS["totobola"], timeout=15, follow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(_decode(resp.content), "html.parser")

    # The same .nextDraw markup is reused by a sidebar jackpot widget for other games; the real
    # Totobola banner is always the first one in document order.
    banner = soup.select_one("em.nextDraw")
    title_el = banner.select_one(".title") if banner else None
    date_el = banner.select_one(".date") if banner else None
    if not title_el or not date_el:
        return []
    m_title = _TOTOBOLA_TITLE.search(title_el.get_text(" ", strip=True))
    m_date = _TOTOBOLA_DATE.search(date_el.get_text(" ", strip=True))
    if not m_title or not m_date:
        return []

    concurso = m_title.group(1)
    deadline_day = _parse_pt_date(m_date.group(1))
    deadline = datetime(
        deadline_day.year, deadline_day.month, deadline_day.day, int(m_date.group(2)), int(m_date.group(3) or 0)
    )
    contest_id = concurso.replace("/", "")

    return [
        Draw(
            game=game,
            concurso=concurso,
            contest_id=contest_id,
            fecha_apostas=deadline,
            data_sorteio=deadline_day + timedelta(days=1),
        )
        for game in ("totobola", "totobola_extra")
    ]


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
