"""Probabilistic-forecast metrics for 1X2 predictions (columns: home, draw, away)."""

import numpy as np

EPS = 1e-12


def log_loss(probs: np.ndarray, outcomes: np.ndarray) -> float:
    return float(-np.mean(np.log(np.clip(probs[np.arange(len(outcomes)), outcomes], EPS, 1))))


def brier(probs: np.ndarray, outcomes: np.ndarray) -> float:
    onehot = np.eye(3)[outcomes]
    return float(np.mean(np.sum((probs - onehot) ** 2, axis=1)))


def rps(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Ranked probability score (outcomes are ordered home < draw < away)."""
    cum_p = np.cumsum(probs, axis=1)[:, :2]
    cum_o = np.cumsum(np.eye(3)[outcomes], axis=1)[:, :2]
    return float(np.mean(np.sum((cum_p - cum_o) ** 2, axis=1) / 2))


def calibration_table(probs: np.ndarray, outcomes: np.ndarray, bins: int = 10) -> list[dict]:
    """Per outcome and probability bin: mean predicted vs observed frequency."""
    rows = []
    edges = np.linspace(0, 1, bins + 1)
    for k, label in enumerate(("1", "X", "2")):
        p = probs[:, k]
        hit = (outcomes == k).astype(float)
        idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
        for b in range(bins):
            mask = idx == b
            if mask.any():
                rows.append(
                    {
                        "outcome": label,
                        "bin": f"{edges[b]:.1f}-{edges[b + 1]:.1f}",
                        "n": int(mask.sum()),
                        "predicted": float(p[mask].mean()),
                        "observed": float(hit[mask].mean()),
                    }
                )
    return rows


def expected_calibration_error(probs: np.ndarray, outcomes: np.ndarray, bins: int = 10) -> float:
    """Sample-weighted mean |predicted - observed| over all outcome/bin cells."""
    table = calibration_table(probs, outcomes, bins)
    total = sum(r["n"] for r in table)
    return float(sum(r["n"] * abs(r["predicted"] - r["observed"]) for r in table) / total)


def summarize(probs: np.ndarray, outcomes: np.ndarray) -> dict[str, float]:
    return {
        "n": len(outcomes),
        "log_loss": log_loss(probs, outcomes),
        "rps": rps(probs, outcomes),
        "brier": brier(probs, outcomes),
        "ece": expected_calibration_error(probs, outcomes),
    }


def binary_summary(p: np.ndarray, y: np.ndarray, bins: int = 10) -> dict[str, float]:
    """Log loss, Brier and calibration error of yes/no forecasts (y in {0, 1})."""
    p = np.clip(p, EPS, 1 - EPS)
    idx = np.clip(np.digitize(p, np.linspace(0, 1, bins + 1)) - 1, 0, bins - 1)
    ece = sum(abs(p[idx == b].mean() - y[idx == b].mean()) * (idx == b).sum() for b in range(bins) if (idx == b).any())
    return {
        "n": len(y),
        "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
        "brier": float(np.mean((p - y) ** 2)),
        "ece": float(ece / len(y)),
    }
