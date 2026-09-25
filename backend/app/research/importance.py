"""How much each criterion drives a fitted model's 1X2 probabilities.

A criterion's weight is the mean absolute change in the three probabilities when
that criterion is neutralized (set to a "no information" value), normalized so
the weights sum to 1. It works for any model with predict(rows).
"""

from dataclasses import replace

import numpy as np

from app.research.features import Rows

# criterion label -> {Rows field: neutral value (None = training mean)}
CRITERIA: dict[str, dict[str, float | None]] = {
    "Força das equipas (Elo)": {"elo_diff": 0.0},
    "Fator casa": {"home_field": 0.0},
    "Ataque recente (golos marcados, últimos 8 jogos)": {"home_for": None, "away_for": None},
    "Defesa recente (golos sofridos, últimos 8 jogos)": {"home_against": None, "away_against": None},
    "Confronto direto (últimos 5 jogos)": {"h2h": 0.0},
}


def criteria_weights(model, rows: Rows) -> dict[str, float]:
    """{criterion: weight in [0, 1]} for the criteria the model actually uses."""
    base = model.predict(rows)
    impact: dict[str, float] = {}
    for label, fields in CRITERIA.items():
        changes = {
            f: np.full_like(getattr(rows, f), getattr(rows, f).mean() if v is None else v) for f, v in fields.items()
        }
        impact[label] = float(np.mean(np.abs(model.predict(replace(rows, **changes)) - base).sum(axis=1)))
    total = sum(impact.values())
    if total == 0:
        return {}
    return {label: v / total for label, v in impact.items() if v / total >= 0.005}
