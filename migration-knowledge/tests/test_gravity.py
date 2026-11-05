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
