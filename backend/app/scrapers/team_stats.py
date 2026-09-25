from datetime import date, timedelta
from typing import Literal

import httpx

from app.cache import TTLCache
from app.config import FOOTBALL_DATA_API_KEY, FOOTBALL_DATA_BASE_URL

_cache = TTLCache(ttl_seconds=3600)

ResultLetter = Literal["W", "D", "L"]


class TeamStatsUnavailable(Exception):
    """Raised when the team/competition isn't covered by the free API tier.

    Callers should fall back to asking the user for manual input.
    """


def _headers() -> dict[str, str]:
    if not FOOTBALL_DATA_API_KEY:
        raise TeamStatsUnavailable("FOOTBALL_DATA_API_KEY not configured")
    return {"X-Auth-Token": FOOTBALL_DATA_API_KEY}


def _get(path: str, params: dict | None = None) -> dict:
    try:
        resp = httpx.get(f"{FOOTBALL_DATA_BASE_URL}{path}", headers=_headers(), params=params, timeout=15)
    except httpx.HTTPError as e:
        raise TeamStatsUnavailable(str(e)) from e

    if resp.status_code == 404:
        raise TeamStatsUnavailable(f"Not found: {path}")
    if resp.status_code == 429:
        raise TeamStatsUnavailable("Rate limited by football-data.org (10 calls/min on free tier)")
    resp.raise_for_status()
    return resp.json()


def find_team_id(team_name: str) -> int | None:
    def _search():
        data = _get("/teams", params={"name": team_name})
        teams = data.get("teams", [])
        return teams[0]["id"] if teams else None

    return _cache.get_or_set(f"team_id:{team_name.lower()}", _search)


def get_recent_results(team_id: int, competition_code: str | None, limit: int) -> list[ResultLetter]:
    """Last `limit` finished matches for the team, most recent first, as W/D/L from the team's perspective."""

    def _fetch():
        params = {"status": "FINISHED", "limit": limit}
        if competition_code:
            params["competitions"] = competition_code
        data = _get(f"/teams/{team_id}/matches", params=params)
        matches = sorted(data.get("matches", []), key=lambda m: m["utcDate"], reverse=True)[:limit]

        results: list[ResultLetter] = []
        for m in matches:
            is_home = m["homeTeam"]["id"] == team_id
            score = m["score"]["fullTime"]
            home_goals, away_goals = score["home"], score["away"]
            if home_goals == away_goals:
                results.append("D")
            elif (home_goals > away_goals) == is_home:
                results.append("W")
            else:
                results.append("L")
        return results

    key = f"recent:{team_id}:{competition_code}:{limit}"
    return _cache.get_or_set(key, _fetch)


def get_head_to_head(team_a_id: int, team_b_id: int, years: int = 5, limit: int = 10) -> list[ResultLetter]:
    """Last `limit` H2H results from team_a's perspective, within the last `years` years."""

    def _fetch():
        date_from = (date.today() - timedelta(days=365 * years)).isoformat()
        data = _get(f"/teams/{team_a_id}/matches", params={"status": "FINISHED", "dateFrom": date_from})
        matches = [
            m
            for m in data.get("matches", [])
            if team_b_id in (m["homeTeam"]["id"], m["awayTeam"]["id"])
        ]
        matches.sort(key=lambda m: m["utcDate"], reverse=True)
        matches = matches[:limit]

        results: list[ResultLetter] = []
        for m in matches:
            is_home = m["homeTeam"]["id"] == team_a_id
            score = m["score"]["fullTime"]
            home_goals, away_goals = score["home"], score["away"]
            if home_goals == away_goals:
                results.append("D")
            elif (home_goals > away_goals) == is_home:
                results.append("W")
            else:
                results.append("L")
        return results

    key = f"h2h:{team_a_id}:{team_b_id}:{years}:{limit}"
    return _cache.get_or_set(key, _fetch)


def get_domestic_standing(team_id: int, competition_code: str) -> int | None:
    """League table position (1 = top), or None if not found."""

    def _fetch():
        data = _get(f"/competitions/{competition_code}/standings")
        for table in data.get("standings", []):
            if table.get("type") != "TOTAL":
                continue
            for row in table.get("table", []):
                if row["team"]["id"] == team_id:
                    return row["position"]
        return None

    key = f"standing:{team_id}:{competition_code}"
    return _cache.get_or_set(key, _fetch)
