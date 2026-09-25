"""How much each criterion drives a fitted model's 1X2 probabilities, and user-scaled criteria.

A criterion's weight is the mean absolute change in the three probabilities when
that criterion is neutralized (set to a "no information" value), normalized so
the weights sum to 1. It works for any model with predict(rows).
"""

from dataclasses import replace

import numpy as np

from app.research.features import Rows

# Stable id -> display label and {Rows field: neutral value (None = mean of the reference rows)}.
CRITERIA: dict[str, dict] = {
    "elo": {"label": "Força das equipas (Elo)", "fields": {"elo_diff": 0.0}},
    "casa": {"label": "Fator casa", "fields": {"home_field": 0.0}},
    "ataque": {
        "label": "Ataque recente (golos marcados, últimos 8 jogos)",
        "fields": {"home_for": None, "away_for": None},
    },
    "defesa": {
        "label": "Defesa recente (golos sofridos, últimos 8 jogos)",
        "fields": {"home_against": None, "away_against": None},
    },
    "h2h": {"label": "Confronto direto (últimos 5 jogos)", "fields": {"h2h": 0.0}},
}

MULTIPLIER_MAX = 2.0


def neutral_values(rows: Rows) -> dict[str, float]:
    """The "no information" value of every criterion field, taken from reference (training) rows."""
    return {
        f: float(getattr(rows, f).mean()) if v is None else v
        for criterion in CRITERIA.values()
        for f, v in criterion["fields"].items()
    }


def apply_multipliers(rows: Rows, multipliers: dict[str, float], neutral: dict[str, float]) -> Rows:
    """x' = neutral + m·(x − neutral) per criterion: m=1 keeps the model, 0 removes the criterion, 2 doubles it."""
    changes = {
        f: neutral[f] + m * (getattr(rows, f) - neutral[f])
        for criterion_id, m in multipliers.items()
        for f in CRITERIA[criterion_id]["fields"]
    }
    return replace(rows, **changes) if changes else rows


def criteria_weights(model, rows: Rows) -> dict[str, float]:
    """{criterion id: weight in [0, 1]} for the criteria the model actually uses."""
    base = model.predict(rows)
    neutral = neutral_values(rows)
    impact = {
        criterion_id: float(np.mean(np.abs(model.predict(apply_multipliers(rows, {criterion_id: 0.0}, neutral)) - base).sum(axis=1)))
        for criterion_id in CRITERIA
    }
    total = sum(impact.values())
    if total == 0:
        return {}
    return {criterion_id: v / total for criterion_id, v in impact.items() if v / total >= 0.005}
