"""Analysis D: unexpectedly strong and weak co-authorship links.

For each pair, observed co-authorship is compared with the baseline model's
expectation. A Poisson reference would declare almost every large pair
"significant" because co-authorship counts are overdispersed, so the reference
distribution is negative binomial (NB2: Var = mu + alpha mu^2), with alpha
estimated by profile maximum likelihood given the baseline means
and parameter uncertainty in mu propagated by drawing coefficient vectors from
their (dyadic-robust) sampling distribution. Two-sided mid-p values are
adjusted with Benjamini-Hochberg across all tested pairs.

Minimum-information rules guard against unstable ratios: a pair is tested only
if its expected count is at least ``min_expected``, and is flagged only if the
log ratio is at least ``min_log_ratio`` in absolute value.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .alignment import bh_adjust
from .gravity import GravityResult, design


def nb2_alpha_moment(y: np.ndarray, mu: np.ndarray) -> float:
    """Cameron-Trivedi auxiliary-regression (moment) estimator of NB2 alpha."""
    z = ((y - mu) ** 2 - y) / np.maximum(mu, 1e-12)
    alpha = float(np.sum(mu * z) / np.sum(mu ** 2))
    return max(alpha, 1e-8)


def nb2_alpha(y: np.ndarray, mu: np.ndarray) -> float:
    """Profile maximum-likelihood NB2 dispersion given the PPML means.

    More efficient than the moment estimator, which is dominated by the few
    largest-mean pairs (checked in tests/test_gravity.py)."""
    from scipy import optimize
    y = np.asarray(y, float)
    if not np.allclose(y, np.round(y)):
        raise ValueError("nb2_alpha needs integer counts (got non-integer values, e.g. fractional counting)")
    mu = np.maximum(np.asarray(mu, float), 1e-12)

    def nll(log_a: float) -> float:
        n, p = _nb(mu, float(np.exp(log_a)))
        return -float(stats.nbinom.logpmf(y, n, p).sum())

    lo, hi = -14.0, 6.0
    res = optimize.minimize_scalar(nll, bounds=(lo, hi), method="bounded")
    if res.x > hi - 1e-3:
        raise ValueError(f"nb2_alpha hit its upper bound (alpha = {np.exp(hi):.0f}); dispersion is not identified")
    return float(np.exp(res.x))


def _nb(mu: np.ndarray, alpha: float):
    n = 1.0 / alpha
    p = n / (n + mu)
    return n, p


def predictive(result: GravityResult, alpha: float, *, draws: int = 500, seed: int = 0,
               chunk: int = 50) -> pd.DataFrame:
    dy = result.extra["dyads"]
    y = result.extra["y"]
    X, names, _, _ = design(dy, result.covariates, result.fe, result.countries)
    beta = result.params[names].to_numpy()
    # Parameter uncertainty for the simulated means uses the full HC1 covariance
    # (fixed effects included). The dyadic-robust covariance exists only for the
    # covariate block; NB2 noise dominates the predictive spread in any case.
    V = result.cov_hc1.loc[names, names].to_numpy()
    rng = np.random.default_rng(seed)
    L = _safe_chol(V)
    F = np.zeros(len(y)); f = np.zeros(len(y))
    mu_draws_q = []
    y_sim = np.zeros((draws, len(y)))
    done = 0
    while done < draws:
        b = min(chunk, draws - done)
        B = beta[None, :] + (rng.standard_normal((b, len(beta))) @ L.T)
        MU = np.exp(X @ B.T)  # (n, b)
        n_, p_ = _nb(MU, alpha)
        F += stats.nbinom.cdf(y[:, None], n_, p_).sum(1)
        f += stats.nbinom.pmf(y[:, None], n_, p_).sum(1)
        y_sim[done:done + b] = rng.negative_binomial(n_, p_).T
        mu_draws_q.append(MU)
        done += b
    F /= draws; f /= draws
    MU_all = np.concatenate(mu_draws_q, axis=1)
    p_lo = F - 0.5 * f          # P(Y < y) + 0.5 P(Y = y)
    p_hi = 1 - F + 0.5 * f      # P(Y > y) + 0.5 P(Y = y)
    p_two = np.minimum(1.0, 2 * np.minimum(p_lo, p_hi))
    mu = result.mu
    out = dy[["a", "b"]].copy()
    out["observed"] = y
    out["expected"] = mu
    out["expected_lo"], out["expected_hi"] = np.quantile(MU_all, [0.025, 0.975], axis=1)
    out["pred_lo"], out["pred_hi"] = np.quantile(y_sim, [0.025, 0.975], axis=0)
    out["log_ratio"] = np.log((y + 0.5) / (mu + 0.5))
    out["pearson_resid_nb"] = (y - mu) / np.sqrt(mu + alpha * mu ** 2)
    out["p_two_sided"] = p_two
    out["direction"] = np.where(y > mu, "stronger", "weaker")
    return out


def flag(pred: pd.DataFrame, *, q: float = 0.05, min_expected: float = 5.0, min_log_ratio: float = np.log(2),
         missing_min_expected: float = 10.0) -> pd.DataFrame:
    out = pred.copy()
    testable = out["expected"] >= min_expected
    out["tested"] = testable
    out["q_bh"] = np.nan
    out.loc[testable, "q_bh"] = bh_adjust(out.loc[testable, "p_two_sided"].to_numpy())
    big = out["log_ratio"].abs() >= min_log_ratio
    sig = out["q_bh"] < q
    out["category"] = "as_expected"
    out.loc[~testable, "category"] = "insufficient_information"
    out.loc[testable & sig & big & (out["direction"] == "stronger"), "category"] = "stronger_than_expected"
    out.loc[testable & sig & big & (out["direction"] == "weaker"), "category"] = "weaker_than_expected"
    out.loc[(out["expected"] >= missing_min_expected) & (out["observed"] == 0), "category"] = "missing_link"
    return out


def _safe_chol(V: np.ndarray) -> np.ndarray:
    w, Q = np.linalg.eigh(0.5 * (V + V.T))
    return Q * np.sqrt(np.clip(w, 0, None))
