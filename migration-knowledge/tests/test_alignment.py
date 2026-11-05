"""Alignment statistics on hand-checkable inputs."""
import numpy as np
import pytest

from src.analysis import alignment as A
from src.networks.build import Layer


def test_jsd_bounds():
    assert A.jsd([1, 2, 3], [2, 4, 6]) == pytest.approx(0.0)
    assert A.jsd([1, 0], [0, 1]) == pytest.approx(1.0)
    assert np.isnan(A.jsd([0, 0], [1, 1]))


def test_topk_overlap_ignores_zeros_and_breaks_ties_by_label():
    labels = ["A", "B", "C", "D"]
    assert A.top_k(np.array([5, 5, 0, 1]), labels, 2) == ["A", "B"]
    assert A.topk_overlap(np.array([5, 4, 0, 1]), np.array([0, 4, 5, 1]), labels, 2) == pytest.approx(0.5)


def test_bh_adjust_matches_reference():
    p = np.array([0.01, 0.04, 0.03, 0.2, np.nan])
    q = A.bh_adjust(p)
    # hand computation: sorted p (.01,.03,.04,.2) -> raw (.04,.06,.0533,.2) -> step-up min
    assert np.allclose(q[:4], [0.04, 0.16 / 3, 0.16 / 3, 0.2])
    assert np.isnan(q[4])
    from statsmodels.stats.multitest import multipletests
    assert np.allclose(q[:4], multipletests(p[:4], method="fdr_bh")[1])


def test_residual_alignment_detects_shared_pair_affinity():
    rng = np.random.default_rng(0)
    n = 30
    nodes = [f"C{i:02d}" for i in range(n)]
    size = rng.lognormal(0, 1, n)
    affinity = rng.normal(0, 1, (n, n)); affinity = (affinity + affinity.T) / 2
    base = np.outer(size, size) * 100
    M = rng.poisson(base * np.exp(affinity)).astype(float); np.fill_diagonal(M, 0)
    Cm = rng.poisson(base * np.exp(affinity)); Cm = np.triu(Cm, 1); Cm = (Cm + Cm.T).astype(float)
    mig, col = Layer("m", nodes, M, True, ""), Layer("c", nodes, Cm, False, "")
    t = A.alignment_table(mig, col, nodes[:5], seed=1, n_perm=200, n_boot=50)
    assert (t["spearman_resid"] > 0.3).all()
    # with independent affinities the residual correlation should be near zero
    aff2 = rng.normal(0, 1, (n, n)); aff2 = (aff2 + aff2.T) / 2
    C2 = rng.poisson(base * np.exp(aff2)); C2 = np.triu(C2, 1); C2 = (C2 + C2.T).astype(float)
    t2 = A.alignment_table(mig, Layer("c", nodes, C2, False, ""), nodes[:5], seed=1, n_perm=200, n_boot=50)
    assert t2["spearman_resid"].abs().median() < 0.3
