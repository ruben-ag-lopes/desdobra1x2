"""Historical match data for backtesting (football-data.co.uk, cached locally as CSV)."""

import csv
import io
import os
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import httpx

# Local CSV cache. On read-only hosts (e.g. Vercel) point DATA_DIR at a writable path such as /tmp/data.
CACHE_DIR = Path(os.environ.get("DATA_DIR") or Path(__file__).resolve().parents[2] / "data")
BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
INTERNATIONAL_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
REFRESH_SECONDS = 12 * 3600  # how long cached files that still change (current season) are trusted


@dataclass
class Match:
    date: datetime
    home: str
    away: str
    home_goals: int
    away_goals: int
    odds: tuple[float, float, float] | None = None  # bookmaker 1/X/2 decimal odds, if present
    neutral: bool = False  # neutral venue: no home advantage
    ou25_odds: tuple[float, float] | None = None  # bookmaker over/under 2.5 goals decimal odds, if present

    @property
    def outcome(self) -> int:
        """0 = home win, 1 = draw, 2 = away win."""
        if self.home_goals > self.away_goals:
            return 0
        return 1 if self.home_goals == self.away_goals else 2


def season_codes(last_start_year: int, n_seasons: int) -> list[str]:
    """e.g. (2024, 3) -> ['2224', '2324', '2425'], oldest first."""
    years = range(last_start_year - n_seasons + 1, last_start_year + 1)
    return [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in years]


def current_season_start(today: date | None = None) -> int:
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def _cached_download(url: str, path: Path, still_changing: bool) -> bytes:
    """Local copy of `url`; re-fetched when stale if the source is still being updated."""
    if path.exists() and not (still_changing and time.time() - path.stat().st_mtime > REFRESH_SECONDS):
        return path.read_bytes()
    try:
        resp = httpx.get(url, timeout=60, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError:
        if path.exists():
            return path.read_bytes()  # offline: keep using the stale copy
        raise
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    return resp.content


def _download(season: str, league: str) -> str:
    still_changing = season == season_codes(current_season_start(), 1)[0]
    content = _cached_download(
        BASE_URL.format(season=season, league=league), CACHE_DIR / f"{league}_{season}.csv", still_changing
    )
    return content.decode("utf-8", errors="replace")


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%d/%m/%Y" if len(value) == 10 else "%d/%m/%y")


def _odds(row: dict) -> tuple[float, float, float] | None:
    for prefix in ("PS", "B365", "BW"):
        try:
            o = (float(row[f"{prefix}H"]), float(row[f"{prefix}D"]), float(row[f"{prefix}A"]))
        except (KeyError, ValueError):
            continue
        if min(o) > 1.0:
            return o
    return None


def _ou25_odds(row: dict) -> tuple[float, float] | None:
    for prefix in ("PC", "AvgC", "P", "Avg", "B365"):  # closing prices first
        try:
            o = (float(row[f"{prefix}>2.5"]), float(row[f"{prefix}<2.5"]))
        except (KeyError, ValueError):
            continue
        if min(o) > 1.0:
            return o
    return None


def load_league(league: str = "P1", last_start_year: int | None = None, n_seasons: int = 8) -> list[Match]:
    """All matches of the last `n_seasons` seasons (default: up to the current one), sorted chronologically."""
    last_start_year = last_start_year or current_season_start()
    matches: list[Match] = []
    for season in season_codes(last_start_year, n_seasons):
        try:
            text = _download(season, league)
        except httpx.HTTPError:
            continue  # season not published yet
        for row in csv.DictReader(io.StringIO(text.lstrip("﻿"))):
            try:
                matches.append(
                    Match(
                        date=_parse_date(row["Date"]),
                        home=row["HomeTeam"].strip(),
                        away=row["AwayTeam"].strip(),
                        home_goals=int(row["FTHG"]),
                        away_goals=int(row["FTAG"]),
                        odds=_odds(row),
                        ou25_odds=_ou25_odds(row),
                    )
                )
            except (KeyError, ValueError):
                continue  # blank/partial rows
    matches.sort(key=lambda m: m.date)
    return matches


def load_international(since_year: int = 2010, exclude_friendlies: bool = False) -> list[Match]:
    """National-team results (martj42/international_results), sorted chronologically."""
    content = _cached_download(INTERNATIONAL_URL, CACHE_DIR / "international_results.csv", still_changing=True)

    matches: list[Match] = []
    for row in csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace"))):
        try:
            played_on = datetime.strptime(row["date"], "%Y-%m-%d")
            if played_on.year < since_year or (exclude_friendlies and row["tournament"] == "Friendly"):
                continue
            matches.append(
                Match(
                    date=played_on,
                    home=row["home_team"],
                    away=row["away_team"],
                    home_goals=int(row["home_score"]),
                    away_goals=int(row["away_score"]),
                    neutral=row["neutral"].upper() == "TRUE",
                )
            )
        except (KeyError, ValueError):
            continue  # fixtures without a score yet
    matches.sort(key=lambda m: m.date)
    return matches
