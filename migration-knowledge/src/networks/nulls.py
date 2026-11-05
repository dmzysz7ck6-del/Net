"""Strength-preserving null models.

The independence (maximum-likelihood configuration) expectation preserves each
node's total connectivity while assuming no pair-specific affinity:

* directed: ``E[i, j] = x_i * y_j`` with ``sum_j E[i, j] = out_i`` and
  ``sum_i E[i, j] = in_j``, zero diagonal (fitted by iterative proportional
  fitting, i.e. RAS);
* undirected: ``E[i, j] = x_i * x_j`` (i != j) with ``sum_j E[i, j] = s_i``
  (the "fitness" solution of the weighted configuration model's expectation).

Comparing an observed layer with ``E`` removes country size. This is the
reference against which "alignment beyond size" (H1) and the topology
comparisons (E2) are judged.
"""
from __future__ import annotations

import numpy as np


def ipf_directed(W: np.ndarray, max_iter: int = 10_000, tol: float = 1e-10) -> np.ndarray:
    W = np.asarray(W, dtype=float)
    n = W.shape[0]
    out_s, in_s = W.sum(1), W.sum(0)
    mask = 1.0 - np.eye(n)
    x = np.where(out_s > 0, 1.0, 0.0)
    y = np.where(in_s > 0, 1.0, 0.0)
    E = np.outer(x, y) * mask
    for _ in range(max_iter):
        rs = E.sum(1)
        x = np.where(rs > 0, x * out_s / np.where(rs > 0, rs, 1), 0.0)
        E = np.outer(x, y) * mask
        cs = E.sum(0)
        y = np.where(cs > 0, y * in_s / np.where(cs > 0, cs, 1), 0.0)
        E = np.outer(x, y) * mask
        err = max(np.abs(E.sum(1) - out_s).max(), np.abs(E.sum(0) - in_s).max())
        if err <= tol * max(1.0, W.sum()):
            break
    return E


def fitness_undirected(W: np.ndarray, max_iter: int = 10_000, tol: float = 1e-10) -> np.ndarray:
    W = np.asarray(W, dtype=float)
    s = W.sum(1)
    total = s.sum()
    x = s / np.sqrt(total) if total > 0 else np.zeros_like(s)
    for _ in range(max_iter):
        denom = x.sum() - x
        x_new = np.where(denom > 0, s / np.where(denom > 0, denom, 1), 0.0)
        # damped update for stability when one node holds most strength
        x_new = 0.5 * x + 0.5 * x_new
        E = np.outer(x_new, x_new)
        np.fill_diagonal(E, 0.0)
        if np.abs(E.sum(1) - s).max() <= tol * max(1.0, total):
            x = x_new
            break
        x = x_new
    E = np.outer(x, x)
    np.fill_diagonal(E, 0.0)
    return E


def expected(W: np.ndarray, directed: bool) -> np.ndarray:
    return ipf_directed(W) if directed else fitness_undirected(W)


def poisson_draw(E: np.ndarray, directed: bool, rng: np.random.Generator) -> np.ndarray:
    """One random network with Poisson weights of mean ``E`` (symmetric if
    undirected). Expected strengths equal observed strengths."""
    if directed:
        D = rng.poisson(E).astype(float)
        np.fill_diagonal(D, 0.0)
        return D
    n = E.shape[0]
    iu = np.triu_indices(n, 1)
    D = np.zeros_like(E)
    D[iu] = rng.poisson(E[iu])
    return D + D.T
