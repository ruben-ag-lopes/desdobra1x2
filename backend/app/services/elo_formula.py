"""Hand-tuned Elo -> 1X2 formula (the pre-backtest engine, kept as fallback and as a baseline)."""

import math

ELO_HOME_ADVANTAGE = 100.0


def elo_1x2(dr: float) -> tuple[float, float, float]:
    """1/X/2 probabilities from an Elo difference (home advantage already included)."""
    expected_home = 1 / (1 + 10 ** (-dr / 400))
    # Draws are most likely between evenly matched sides and fade with the gap.
    prob_draw = 0.10 + 0.20 * math.exp(-((dr / 300) ** 2))
    prob_home = max(0.02, expected_home - prob_draw / 2)
    prob_away = max(0.02, 1 - expected_home - prob_draw / 2)
    total = prob_home + prob_draw + prob_away
    return prob_home / total, prob_draw / total, prob_away / total
