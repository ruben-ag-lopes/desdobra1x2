"""Optional BigQuery sink for predictions (live app and backtests).

Enabled only when GCP_PROJECT and BQ_DATASET are set and google-cloud-bigquery is
installed; credentials come from Application Default Credentials
(`gcloud auth application-default login` or GOOGLE_APPLICATION_CREDENTIALS).
Otherwise every call is a no-op, so the app works the same without it.
"""

import logging
import os
import uuid
from datetime import date, datetime, timezone

log = logging.getLogger(__name__)

PREDICTIONS_TABLE = "predictions"
BACKTEST_TABLE = "backtest_predictions"

_PREDICTION_FIELDS = [
    ("prediction_id", "STRING"),
    ("created_at", "TIMESTAMP"),
    ("concurso", "STRING"),
    ("match_date", "DATE"),
    ("home_team", "STRING"),
    ("away_team", "STRING"),
    ("p_home", "FLOAT"),
    ("p_draw", "FLOAT"),
    ("p_away", "FLOAT"),
    ("fixed_result", "STRING"),
    ("model_version", "STRING"),
]
_BACKTEST_FIELDS = [
    ("run_id", "STRING"),
    ("created_at", "TIMESTAMP"),
    ("dataset", "STRING"),
    ("match_date", "DATE"),
    ("home_team", "STRING"),
    ("away_team", "STRING"),
    ("outcome", "STRING"),
    ("p_home", "FLOAT"),
    ("p_draw", "FLOAT"),
    ("p_away", "FLOAT"),
    ("model_version", "STRING"),
]

_client = None
_ready_tables: set[str] = set()


def enabled() -> bool:
    return bool(os.environ.get("GCP_PROJECT") and os.environ.get("BQ_DATASET"))


def _table(name: str, fields: list[tuple[str, str]]):
    global _client
    from google.cloud import bigquery  # optional dependency, imported only when enabled

    if _client is None:
        _client = bigquery.Client(project=os.environ["GCP_PROJECT"])
    table_id = f"{os.environ['GCP_PROJECT']}.{os.environ['BQ_DATASET']}.{name}"
    if table_id not in _ready_tables:
        _client.create_dataset(f"{os.environ['GCP_PROJECT']}.{os.environ['BQ_DATASET']}", exists_ok=True)
        schema = [bigquery.SchemaField(n, t) for n, t in fields]
        _client.create_table(bigquery.Table(table_id, schema=schema), exists_ok=True)
        _ready_tables.add(table_id)
    return table_id


def _insert(name: str, fields: list[tuple[str, str]], rows: list[dict]) -> None:
    if not enabled() or not rows:
        return
    try:
        table_id = _table(name, fields)
        for start in range(0, len(rows), 500):
            errors = _client.insert_rows_json(table_id, rows[start : start + 500])
            if errors:
                log.warning("BigQuery insert errors for %s: %s", table_id, errors[:3])
                return
    except Exception:
        log.exception("BigQuery write to %s failed", name)  # never break the request


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_predictions(probabilities, concurso: str | None, match_date: date | None) -> None:
    """Store the 1X2 probabilities shown to the user, with the model version that produced them."""
    created = _now()
    rows = [
        {
            "prediction_id": str(uuid.uuid4()),
            "created_at": created,
            "concurso": concurso,
            "match_date": match_date.isoformat() if match_date else None,
            "home_team": p.home_team,
            "away_team": p.away_team,
            "p_home": p.prob_home,
            "p_draw": p.prob_draw,
            "p_away": p.prob_away,
            "fixed_result": "".join(p.fixed_results) or None,
            "model_version": p.modelo,
        }
        for p in probabilities
    ]
    _insert(PREDICTIONS_TABLE, _PREDICTION_FIELDS, rows)


def log_backtest(dataset: str, matches, probs_by_model: dict, idx) -> str | None:
    """Store every out-of-sample backtest prediction; returns the run id (None when disabled)."""
    if not enabled():
        return None
    run_id = str(uuid.uuid4())
    created = _now()
    rows = []
    for name, probs in probs_by_model.items():
        for p, i in zip(probs, idx):
            m = matches[i]
            rows.append(
                {
                    "run_id": run_id,
                    "created_at": created,
                    "dataset": dataset,
                    "match_date": m.date.date().isoformat(),
                    "home_team": m.home,
                    "away_team": m.away,
                    "outcome": "1X2"[m.outcome],
                    "p_home": float(p[0]),
                    "p_draw": float(p[1]),
                    "p_away": float(p[2]),
                    "model_version": name,
                }
            )
    _insert(BACKTEST_TABLE, _BACKTEST_FIELDS, rows)
    return run_id
