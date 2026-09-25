"""How much each criterion drives a fitted model's 1X2 probabilities.

A criterion's weight is the mean absolute change in the three probabilities when
that criterion is neutralized (set to a "no information" value), normalized so
the weights sum to 1. It works for any model with predict(rows).
"""

from dataclasses import replace

import numpy as np

from app.research.features import Rows

# Stable IDs for criteria used in API and user customization.
# Each ID maps to: label (for display), fields (Rows attributes), neutral values.
CRITERIA: dict[str, dict] = {
    "elo": {
        "label": "Força das equipas (Elo)",
        "fields": {"elo_diff": 0.0},
    },
    "casa": {
        "label": "Fator casa",
        "fields": {"home_field": 0.0},
    },
    "ataque": {
        "label": "Ataque recente (golos marcados, últimos 8 jogos)",
        "fields": {"home_for": None, "away_for": None},
    },
    "defesa": {
        "label": "Defesa recente (golos sofridos, últimos 8 jogos)",
        "fields": {"home_against": None, "away_against": None},
    },
    "h2h": {
        "label": "Confronto direto (últimos 5 jogos)",
        "fields": {"h2h": 0.0},
    },
}

# Backwards compat: label -> id
_LABEL_TO_ID = {v["label"]: k for k, v in CRITERIA.items()}


def criteria_weights(model, rows: Rows) -> dict[str, float]:
    """{criterion id: weight in [0, 1]} for the criteria the model actually uses."""
    base = model.predict(rows)
    impact: dict[str, float] = {}
    for crit_id, crit_info in CRITERIA.items():
        fields = crit_info["fields"]
        changes = {
            f: np.full_like(getattr(rows, f), getattr(rows, f).mean() if v is None else v)
            for f, v in fields.items()
        }
        impact[crit_id] = float(np.mean(np.abs(model.predict(replace(rows, **changes)) - base).sum(axis=1)))
    total = sum(impact.values())
    if total == 0:
        return {}
    return {crit_id: v / total for crit_id, v in impact.items() if v / total >= 0.005}


def apply_multipliers(rows: Rows, multipliers: dict[str, float], training_means: dict[str, float] | None = None) -> Rows:
    """Apply criterion multipliers to rows: x' = neutral + m * (x - neutral).

    Args:
        rows: input feature rows.
        multipliers: {criterion_id: multiplier in [0, 2]}, where 1.0 = default.
        training_means: {field_name: training mean}, for criteria with None neutral.
                       If None, uses rows' attribute means.

    Returns:
        Modified rows with adjusted criteria.

    Raises:
        ValueError: if a multiplier is out of range or criterion_id is unknown.
    """
    training_means = training_means or {}
    changes = {}

    for crit_id, mult in multipliers.items():
        if crit_id not in CRITERIA:
            raise ValueError(f"Unknown criterion: {crit_id}")
        if not 0 <= mult <= 2:
            raise ValueError(f"Multiplier out of range [0, 2]: {crit_id}={mult}")

        crit_info = CRITERIA[crit_id]
        fields = crit_info["fields"]

        for field_name, neutral_val in fields.items():
            current = getattr(rows, field_name)
            if neutral_val is None:
                neutral = training_means.get(field_name, current.mean())
            else:
                neutral = neutral_val

            adjusted = neutral + mult * (current - neutral)
            changes[field_name] = adjusted

    return replace(rows, **changes) if changes else rows
