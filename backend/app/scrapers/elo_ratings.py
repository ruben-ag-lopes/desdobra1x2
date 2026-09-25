"""Team strength from public Elo ratings (no API key required).

National teams: eloratings.net. Clubs: clubelo.com (best effort; the service is
sometimes down, in which case callers fall back to the criteria-based model).
"""

import csv
import io
import unicodedata

import httpx

from app.cache import TTLCache

_cache = TTLCache(ttl_seconds=6 * 3600)

# Portuguese (Santa Casa) name -> English name used by eloratings.net
_PT_TO_EN = {
    "alemanha": "Germany", "albania": "Albania", "andorra": "Andorra", "arménia": "Armenia",
    "armenia": "Armenia", "áustria": "Austria", "austria": "Austria", "azerbaijão": "Azerbaijan",
    "azerbaijao": "Azerbaijan", "bélgica": "Belgium", "belgica": "Belgium",
    "bielorrússia": "Belarus", "bielorrussia": "Belarus", "bósnia": "Bosnia and Herzegovina",
    "bosnia": "Bosnia and Herzegovina", "bósnia-herzegovina": "Bosnia and Herzegovina",
    "bulgária": "Bulgaria", "bulgaria": "Bulgaria", "chipre": "Cyprus", "chéquia": "Czechia",
    "chequia": "Czechia", "república checa": "Czechia", "croácia": "Croatia", "croacia": "Croatia",
    "dinamarca": "Denmark", "eslováquia": "Slovakia", "eslovaquia": "Slovakia",
    "eslovénia": "Slovenia", "eslovenia": "Slovenia", "espanha": "Spain", "estónia": "Estonia",
    "estonia": "Estonia", "finlândia": "Finland", "finlandia": "Finland", "frança": "France",
    "franca": "France", "geórgia": "Georgia", "georgia": "Georgia", "gibraltar": "Gibraltar",
    "grécia": "Greece", "grecia": "Greece", "hungria": "Hungary", "inglaterra": "England",
    "irlanda": "Ireland", "irlanda do norte": "Northern Ireland", "islândia": "Iceland",
    "islandia": "Iceland", "israel": "Israel", "itália": "Italy", "italia": "Italy",
    "kosovo": "Kosovo", "letónia": "Latvia", "letonia": "Latvia", "liechtenstein": "Liechtenstein",
    "lituânia": "Lithuania", "lituania": "Lithuania", "luxemburgo": "Luxembourg",
    "malta": "Malta", "moldávia": "Moldova", "moldavia": "Moldova", "montenegro": "Montenegro",
    "macedónia do norte": "North Macedonia", "macedonia do norte": "North Macedonia",
    "noruega": "Norway", "países baixos": "Netherlands", "paises baixos": "Netherlands",
    "holanda": "Netherlands", "país de gales": "Wales", "pais de gales": "Wales", "gales": "Wales",
    "polónia": "Poland", "polonia": "Poland", "portugal": "Portugal", "roménia": "Romania",
    "romenia": "Romania", "escócia": "Scotland", "escocia": "Scotland", "sérvia": "Serbia",
    "servia": "Serbia", "san marino": "San Marino", "suécia": "Sweden", "suecia": "Sweden",
    "suíça": "Switzerland", "suica": "Switzerland", "turquia": "Turkey", "ucrânia": "Ukraine",
    "ucrania": "Ukraine", "faroé": "Faroe Islands", "ilhas faroé": "Faroe Islands",
    "brasil": "Brazil", "argentina": "Argentina", "uruguai": "Uruguay", "colômbia": "Colombia",
    "colombia": "Colombia", "méxico": "Mexico", "mexico": "Mexico", "estados unidos": "United States",
    "japão": "Japan", "japao": "Japan", "marrocos": "Morocco", "senegal": "Senegal",
    "canadá": "Canada", "canada": "Canada", "coreia do sul": "South Korea", "austrália": "Australia",
    "australia": "Australia", "equador": "Ecuador", "paraguai": "Paraguay", "chile": "Chile",
}

# Clubs whose Santa Casa name differs from the clubelo.com name.
_CLUB_ALIASES = {
    "sporting": "Sporting", "sporting cp": "Sporting", "fc porto": "Porto", "porto": "Porto",
    "sl benfica": "Benfica", "benfica": "Benfica", "sc braga": "Braga", "braga": "Braga",
    "vitória sc": "Guimaraes", "vitoria sc": "Guimaraes", "v. guimarães": "Guimaraes",
    "man. city": "Man City", "manchester city": "Man City", "man. united": "Man United",
    "manchester united": "Man United", "atlético madrid": "Atletico", "atl. madrid": "Atletico",
    "real madrid": "Real Madrid", "barcelona": "Barcelona", "bayern munique": "Bayern",
    "bayern": "Bayern", "inter": "Inter", "inter milão": "Inter", "ac milan": "Milan",
    "juventus": "Juventus", "nápoles": "Napoli", "napoles": "Napoli", "psg": "Paris SG",
    "paris sg": "Paris SG", "b. dortmund": "Dortmund", "borussia dortmund": "Dortmund",
}


def _norm(name: str) -> str:
    return " ".join(name.lower().split())


def _strip_accents(name: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn")


def _national_table() -> dict[str, float]:
    """English team name (lowercase) -> Elo."""

    def _fetch() -> dict[str, float]:
        names_resp = httpx.get("https://www.eloratings.net/en.teams.tsv", timeout=15)
        ratings_resp = httpx.get("https://www.eloratings.net/World.tsv", timeout=15)
        names_resp.raise_for_status()
        ratings_resp.raise_for_status()

        code_to_names: dict[str, list[str]] = {}
        for line in names_resp.text.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                code_to_names[parts[0]] = [p.strip().lower() for p in parts[1:] if p.strip()]

        table: dict[str, float] = {}
        for line in ratings_resp.text.splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            code, elo = parts[2], parts[3]
            for name in code_to_names.get(code, []):
                table[name] = float(elo)
        return table

    return _cache.get_or_set("national_elo", _fetch)


def _national_elo(name: str) -> float | None:
    key = _norm(name)
    en = _PT_TO_EN.get(key) or _PT_TO_EN.get(_strip_accents(key))
    if not en:
        return None
    try:
        return _national_table().get(en.lower())
    except Exception:
        return None


def _club_elo(name: str) -> float | None:
    query = _CLUB_ALIASES.get(_norm(name), name).replace(" ", "")

    def _fetch() -> float | None:
        try:
            resp = httpx.get(f"http://api.clubelo.com/{query}", timeout=8)
            resp.raise_for_status()
            rows = list(csv.DictReader(io.StringIO(resp.text)))
            return float(rows[-1]["Elo"]) if rows else None
        except Exception:
            return None  # cached too, so a dead service doesn't slow every request

    return _cache.get_or_set(f"club_elo:{query.lower()}", _fetch)


def get_elo(team: str) -> float | None:
    """Elo rating for a national team or club, or None if unknown."""
    return _national_elo(team) or _club_elo(team)
