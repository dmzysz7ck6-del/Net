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
    t2 = A.alignment_table(mig, Layer("c", nodes, C2, False, ""), nodes, seed=1, n_perm=200, n_boot=0)
    assert abs(t2["spearman_resid"].median()) < 0.15     # signed median over all 30 origins
    assert abs(t2["rho_excess"].median()) < 0.15
    assert (t2["q_sim_resid"] < 0.05).mean() <= 0.1
    assert (t["rho_excess"] > 0.2).all()


def test_size_artefact_is_removed_by_simulation_null():
    """Sparse layers with NO shared affinity: zero cells give size-dependent
    residuals in both layers, so the raw residual rho is biased upward; the
    size-preserving simulation null must absorb it."""
    rng = np.random.default_rng(7)
    n = 60
    nodes = [f"C{i:02d}" for i in range(n)]
    size = rng.lognormal(0, 1.5, n)
    base = np.outer(size, size)
    M = rng.poisson(0.3 * base * np.exp(rng.normal(0, 1, (n, n)))).astype(float); np.fill_diagonal(M, 0)
    Cm = rng.poisson(0.3 * base * np.exp(rng.normal(0, 1, (n, n)))); Cm = np.triu(Cm, 1); Cm = (Cm + Cm.T).astype(float)
    t = A.alignment_table(Layer("m", nodes, M, True, ""), Layer("c", nodes, Cm, False, ""), nodes[:20], seed=3, n_perm=300, n_boot=0)
    assert t["spearman_resid"].median() > 0.1           # the artefact exists
    assert abs(t["rho_excess"].median()) < 0.1          # and is removed


def test_rarefied_jsd_removes_sample_size_bias():
    """Every origin's collaboration is drawn from exactly its migration
    distribution (true JSD = 0) but origins differ in paper counts: the plug-in
    JSD falls with N (spurious support for H2); the rarefied JSD does not."""
    from scipy import stats as st
    rng = np.random.default_rng(5)
    n = 80
    nodes = [f"C{i:02d}" for i in range(n)]
    sizes = np.exp(rng.uniform(np.log(60), np.log(20000), n)).astype(int)
    M = np.zeros((n, n)); C = np.zeros((n, n))
    for o in range(n):
        q = rng.dirichlet(np.full(n, 0.5)); q[o] = 0; q /= q.sum()
        M[o] = q * 1e6
        C[o] = rng.multinomial(sizes[o], q)
    mig, col = Layer("m", nodes, M, True, ""), Layer("c", nodes, C, False, "")
    t = A.alignment_table(mig, col, nodes, seed=2, n_perm=0, n_boot=0, rarefy_n=50)
    r_plugin = st.spearmanr(t["jsd_raw"], sizes).statistic
    r_rare = st.spearmanr(t["jsd_rarefied"], sizes).statistic
    assert r_plugin < -0.5
    assert abs(r_rare) < 0.25
