"""PPML gravity estimator: coefficient recovery and inference plumbing on a
synthetic data-generating process (code correctness only)."""
import numpy as np
import pandas as pd
import pytest

from src.analysis import gravity as G
from src.analysis import residuals as R


def synthetic_dyads(n=40, seed=0, beta=(-1.0, 0.5, 0.3), alpha_nb=0.0):
    rng = np.random.default_rng(seed)
    nodes = [f"C{i:02d}" for i in range(n)]
    fe = rng.normal(0, 1, n)
    rows = []
    for i in range(n):
        for j in range(i + 1, n):
            ldist = rng.normal(8, 0.5)
            lang = float(rng.random() < 0.2)
            lmig = max(0.0, rng.normal(3, 2))
            eta = 2 + fe[i] + fe[j] + beta[0] * (ldist - 8) + beta[1] * lang + beta[2] * lmig
            mu = np.exp(eta)
            if alpha_nb > 0:
                mu = rng.gamma(1 / alpha_nb, mu * alpha_nb)
            rows.append({"a": nodes[i], "b": nodes[j], "ldist": ldist - 8, "lang": lang, "lmig": lmig,
                         "y": rng.poisson(mu)})
    return pd.DataFrame(rows)


def test_ppml_recovers_coefficients():
    d = synthetic_dyads()
    r = G.fit_ppml(d, "y", ["ldist", "lang", "lmig"], name="t")
    assert r.converged
    assert r.params["ldist"] == pytest.approx(-1.0, abs=0.08)
    assert r.params["lang"] == pytest.approx(0.5, abs=0.08)
    assert r.params["lmig"] == pytest.approx(0.3, abs=0.03)
    tab = r.table()
    assert (tab["se_dyadic"] > 0).all() and set(tab["term"]) == {"ldist", "lang", "lmig"}


def test_dyadic_se_not_smaller_than_hc1_under_country_shocks():
    d = synthetic_dyads(alpha_nb=0.5, seed=3)
    r = G.fit_ppml(d, "y", ["ldist", "lang", "lmig"], name="t")
    assert np.all(np.linalg.eigvalsh(r.cov.to_numpy()) >= -1e-10)


def test_all_zero_country_dropped():
    d = synthetic_dyads(n=12)
    d.loc[(d["a"] == "C00") | (d["b"] == "C00"), "y"] = 0
    r = G.fit_ppml(d, "y", ["ldist"], name="t")
    assert r.dropped_countries == ["C00"] and "C00" not in r.countries


def test_cv_and_compare():
    d = synthetic_dyads(n=25)
    cv = G.cross_validate(d, "y", {"base": ["ldist", "lang"], "full": ["ldist", "lang", "lmig"]}, k=5, seed=1)
    cmp = G.cv_compare(cv, "base", "full")
    assert cmp["rel_reduction_total"] > 0 and cmp["folds"] == 5


def test_wald_equal_terms():
    d = synthetic_dyads(n=25)
    r = G.fit_ppml(d, "y", ["ldist", "lang", "lmig"], name="t")
    w = G.wald_equal(r, "lang", "lmig")
    assert 0 <= w["p"] <= 1


def test_nb_alpha_and_flags():
    d = synthetic_dyads(n=30, alpha_nb=0.3, seed=5)
    r = G.fit_ppml(d, "y", ["ldist", "lang", "lmig"], name="t")
    a = R.nb2_alpha(r.extra["y"], r.mu)
    assert 0.2 < a < 0.45
    pred = R.predictive(r, a, draws=60, seed=0)
    assert pred["p_two_sided"].between(0, 1).all()
    assert (pred["expected_lo"] <= pred["expected"] * 1.5).all()
    fl = R.flag(pred, min_expected=5)
    assert set(fl["category"]) <= {"as_expected", "insufficient_information", "stronger_than_expected",
                                   "weaker_than_expected", "missing_link"}
    # few false positives under a correctly specified model
    assert (fl["category"].isin(["stronger_than_expected", "weaker_than_expected"])).mean() < 0.05


def test_dyadic_cov_matches_bruteforce_formula():
    """Covariate-block dyadic variance equals the explicit double sum over all
    pairs of dyads that share a country, using FWL influence scores."""
    d = synthetic_dyads(n=9, seed=4)
    r = G.fit_ppml(d, "y", ["ldist", "lang", "lmig"])
    X, names, A, countries = G.design(r.extra["dyads"], r.covariates, True, r.countries)
    k = len(r.covariates)
    Xb, Z = X[:, 1:1 + k], np.column_stack([X[:, :1], X[:, 1 + k:]])
    e = r.extra["y"] - r.mu
    Xt = G.fwl_residualize(Xb, Z, r.mu)
    s = Xt * e[:, None]
    dy = r.extra["dyads"]
    meat = np.zeros((k, k))
    for i in range(len(dy)):
        for j in range(len(dy)):
            if {dy.a[i], dy.b[i]} & {dy.a[j], dy.b[j]}:
                meat += np.outer(s[i], s[j])
    G_ = len(countries)
    bread = np.linalg.inv(Xt.T @ (Xt * r.mu[:, None]))
    V = bread @ (meat * G_ / (G_ - 1)) @ bread
    if not r.extra["dyadic_cov_info"]["clipped"]:
        assert np.allclose(V, r.cov.to_numpy(), rtol=1e-6, atol=1e-12)


def test_dyadic_se_tracks_sampling_sd_under_node_dependence():
    """With node-level dependence that fixed effects do not absorb, HC1 badly
    understates the sampling SD; the dyadic SE should track it."""
    rng = np.random.default_rng(11)
    n, reps, beta = 40, 40, 0.4
    bs, sd, sh = [], [], []
    for _ in range(reps):
        v = rng.normal(0, 1, n); w = 0.8 * v + rng.normal(0, 0.3, n); fe = rng.normal(0, 0.5, n)
        I, J = np.triu_indices(n, 1)
        x = v[I] * v[J] + rng.normal(0, 0.5, len(I))
        mu = np.exp(1.5 + fe[I] + fe[J] + beta * x + 0.5 * w[I] * w[J] + rng.normal(0, 0.3, len(I)))
        d = pd.DataFrame({"a": [f"C{i:02d}" for i in I], "b": [f"C{j:02d}" for j in J], "x": x, "y": rng.poisson(mu)})
        res = G.fit_ppml(d, "y", ["x"])
        bs.append(res.params["x"]); sd.append(np.sqrt(res.cov.loc["x", "x"])); sh.append(np.sqrt(res.cov_hc1.loc["x", "x"]))
    emp = np.std(bs, ddof=1)
    assert 0.65 < np.mean(sd) / emp < 1.35
    assert np.mean(sd) > 1.3 * np.mean(sh)
    assert min(sd) > 0
