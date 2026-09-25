"""1X2 models compared in the backtest. Each has fit(rows) and predict(rows) -> (n, 3) array."""

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit, gammaln

from app.research.features import Rows
from app.services.elo_formula import ELO_HOME_ADVANTAGE, elo_1x2

MAX_GOALS = 10


class FrequencyModel:
    """Baseline: historical 1/X/2 frequencies, ignoring the teams."""

    name = "frequencias"

    def fit(self, rows: Rows) -> None:
        self.freq = np.bincount(rows.outcome, minlength=3) / len(rows.outcome)

    def predict(self, rows: Rows) -> np.ndarray:
        return np.tile(self.freq, (len(rows.outcome), 1))


class CurrentEngineModel:
    """The formula currently used in totobola_engine (no fitting), for reference."""

    name = "motor_atual"

    def fit(self, rows: Rows) -> None:
        pass

    def predict(self, rows: Rows) -> np.ndarray:
        return np.array([elo_1x2(d + ELO_HOME_ADVANTAGE * h) for d, h in zip(rows.elo_diff, rows.home_field)])


class OrderedLogitElo:
    """Elo difference -> 1X2 through an ordered logit whose parameters are fitted."""

    name = "elo_calibrado"

    def fit(self, rows: Rows) -> None:
        d, hf = rows.elo_diff / 400, rows.home_field
        y = rows.outcome

        def nll(params):
            p = self._probs(d, hf, *params)
            return -np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)))

        self.params = minimize(nll, x0=[1.0, 0.3, 0.6], method="Nelder-Mead").x

    @staticmethod
    def _probs(d, hf, beta, home, theta):
        theta = abs(theta)
        z = beta * d + home * hf
        p_home = expit(z - theta)
        p_away = expit(-z - theta)
        return np.column_stack([p_home, 1 - p_home - p_away, p_away])

    def predict(self, rows: Rows) -> np.ndarray:
        return self._probs(rows.elo_diff / 400, rows.home_field, *self.params)


def _design(rows: Rows, side: str, use_h2h: bool) -> np.ndarray:
    d = rows.elo_diff / 400
    if side == "home":
        cols = [np.ones_like(d), rows.home_field, d, rows.home_for, rows.away_against]
        if use_h2h:
            cols.append(rows.h2h)
    else:
        cols = [np.ones_like(d), rows.home_field, -d, rows.away_for, rows.home_against]
        if use_h2h:
            cols.append(-rows.h2h)
    return np.column_stack(cols)


def _fit_poisson(X: np.ndarray, y: np.ndarray, l2: float = 1e-3) -> np.ndarray:
    def fun(b):
        eta = np.clip(X @ b, -10, 10)
        mu = np.exp(eta)
        value = np.sum(mu - y * eta) + 0.5 * l2 * np.sum(b[1:] ** 2)
        grad = X.T @ (mu - y) + l2 * np.r_[0.0, b[1:]]
        return value, grad

    return minimize(fun, x0=np.zeros(X.shape[1]), jac=True, method="L-BFGS-B").x


def _pmf(mu: np.ndarray) -> np.ndarray:
    g = np.arange(MAX_GOALS + 1)
    return np.exp(g * np.log(mu)[:, None] - mu[:, None] - gammaln(g + 1))


def _dc_tau(lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    """Dixon-Coles adjustment matrix (n, G, G); identity (all ones) when rho = 0."""
    tau = np.ones((len(lam), MAX_GOALS + 1, MAX_GOALS + 1))
    tau[:, 0, 0] = 1 - lam * mu * rho
    tau[:, 0, 1] = 1 + lam * rho
    tau[:, 1, 0] = 1 + mu * rho
    tau[:, 1, 1] = 1 - rho
    return tau


def _score_matrix(lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    m = _pmf(lam)[:, :, None] * _pmf(mu)[:, None, :]
    return m * _dc_tau(lam, mu, rho)


class PoissonModel:
    """Expected goals per side from Elo + recent goals (+ optional H2H), Poisson score grid -> 1X2."""

    def __init__(self, use_h2h: bool = False, dixon_coles: bool = False):
        self.use_h2h = use_h2h
        self.dixon_coles = dixon_coles
        self.rho = 0.0
        self.name = "poisson" + ("+h2h" if use_h2h else "") + ("+dixon_coles" if dixon_coles else "")

    def _lambdas(self, rows: Rows) -> tuple[np.ndarray, np.ndarray]:
        lam = np.exp(np.clip(_design(rows, "home", self.use_h2h) @ self.beta_home, -10, 10))
        mu = np.exp(np.clip(_design(rows, "away", self.use_h2h) @ self.beta_away, -10, 10))
        return lam, mu

    def fit(self, rows: Rows) -> None:
        self.beta_home = _fit_poisson(_design(rows, "home", self.use_h2h), rows.home_goals)
        self.beta_away = _fit_poisson(_design(rows, "away", self.use_h2h), rows.away_goals)
        self.rho = 0.0
        if self.dixon_coles:
            lam, mu = self._lambdas(rows)
            hg = rows.home_goals.astype(int).clip(0, MAX_GOALS)
            ag = rows.away_goals.astype(int).clip(0, MAX_GOALS)
            idx = np.arange(len(hg))

            def nll(rho):
                grid = _score_matrix(lam, mu, rho)
                return -np.mean(np.log(np.clip(grid[idx, hg, ag], 1e-12, None)))

            self.rho = float(minimize_scalar(nll, bounds=(-0.3, 0.3), method="bounded").x)

    def score_grid(self, rows: Rows) -> np.ndarray:
        """(n, G, G) probabilities of each exact score; [i, h, a] = home h goals, away a goals."""
        lam, mu = self._lambdas(rows)
        grid = _score_matrix(lam, mu, self.rho)
        return grid / grid.sum(axis=(1, 2), keepdims=True)

    def goal_markets(self, rows: Rows) -> dict[str, np.ndarray]:
        """P(over 2.5 goals) and P(both teams score), from the score grid."""
        grid = self.score_grid(rows)
        g = np.arange(MAX_GOALS + 1)
        total = g[:, None] + g[None, :]
        return {
            "over25": grid[:, total >= 3].sum(axis=1),
            "btts": grid[:, 1:, 1:].sum(axis=(1, 2)),
        }

    def predict(self, rows: Rows) -> np.ndarray:
        grid = self.score_grid(rows)
        home = np.tril(grid, k=-1).sum(axis=(1, 2))  # home goals > away goals
        draw = np.trace(grid, axis1=1, axis2=2)
        away = np.triu(grid, k=1).sum(axis=(1, 2))
        probs = np.column_stack([home, draw, away])
        return probs / probs.sum(axis=1, keepdims=True)


def all_models() -> list:
    return [
        FrequencyModel(),
        CurrentEngineModel(),
        OrderedLogitElo(),
        PoissonModel(),
        PoissonModel(use_h2h=True),
        PoissonModel(dixon_coles=True),
        PoissonModel(use_h2h=True, dixon_coles=True),
    ]
