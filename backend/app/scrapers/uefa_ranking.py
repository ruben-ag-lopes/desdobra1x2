# UEFA country coefficient ranking (2025/2026 cycle, top associations).
# Stable across a season; update yearly from uefa.com club coefficients page.
# Rank 1 = strongest. Countries not listed are treated as unranked (weakest).
UEFA_COUNTRY_RANKING: dict[str, int] = {
    "England": 1,
    "Spain": 2,
    "Italy": 3,
    "Germany": 4,
    "France": 5,
    "Netherlands": 6,
    "Portugal": 7,
    "Belgium": 8,
    "Turkey": 9,
    "Austria": 10,
    "Czech Republic": 11,
    "Switzerland": 12,
    "Greece": 13,
    "Scotland": 14,
    "Denmark": 15,
    "Serbia": 16,
    "Croatia": 17,
    "Norway": 18,
    "Ukraine": 19,
    "Israel": 20,
    "Poland": 21,
    "Cyprus": 22,
    "Sweden": 23,
    "Romania": 24,
    "Azerbaijan": 25,
}

TOP_TIER_CUTOFF = 3
UNRANKED_POSITION = 99


def get_rank(country: str) -> int:
    return UEFA_COUNTRY_RANKING.get(country, UNRANKED_POSITION)


def rank_to_score(rank: int) -> float:
    """Higher score = stronger country. Normalized roughly to [0, 1], with a bonus for top-3."""
    base = max(0.0, 1.0 - (rank - 1) / 30)
    bonus = 0.15 if rank <= TOP_TIER_CUTOFF else 0.0
    return min(1.0, base + bonus)
