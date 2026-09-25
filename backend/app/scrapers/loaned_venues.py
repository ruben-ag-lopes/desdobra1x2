# Portuguese (and other) clubs known to play "home" matches at a borrowed/rented
# stadium rather than their own — the home-advantage bonus should NOT apply here.
# Extend this list as needed; it is not exhaustive.
LOANED_VENUE_TEAMS: set[str] = {
    "torreense",
    "casa pia",
    "casa pia ac",
    "lourosa",
    "uniao de leiria",
    "união de leiria",
    "oliveirense",
    "belenenses",
    "sporting cp b",
}


def plays_at_loaned_venue(team_name: str) -> bool:
    return team_name.strip().lower() in LOANED_VENUE_TEAMS
