"""Analysis B/C: gravity models of bilateral co-authorship.

Estimator: Poisson pseudo-maximum likelihood (PPML; Santos Silva & Tenreyro
2006), which is consistent for the conditional mean under heteroskedasticity
and handles zero counts. The outcome is undirected, so each country has a
single fixed effect that enters whichever position it holds in the pair:

    ln mu_ij = a_i + a_j + x_ij' b

Country fixed effects absorb research output, GDP, population and every other
monadic attribute, which is why masses are not entered separately in the
confirmatory models (an interpretable no-FE "mass" model is also provided).

Inference: dyadic-robust covariance (Fafchamps & Gubert 2007; Cameron & Miller
2014; Aronow, Samii & Assenova 2015): scores of any two pairs that share a
country may be correlated. It is computed for the covariate coefficients from
their influence functions after partialling out the intercept and fixed
effects (FWL): Meat = sum_c S_c S_c' - sum_d s_d s_d' where S_c sums the
influence scores of all pairs containing country c, with a G/(G-1) factor.
(The full-matrix version is indefinite: by the first-order conditions every
country's score sum in the fixed-effect directions is exactly zero.)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


@dataclass
class GravityResult:
    name: str
    params: pd.Series
    cov: pd.DataFrame          # dyadic-robust, covariate coefficients only
    cov_hc1: pd.DataFrame      # HC1, full parameter vector (intercept, covariates, FE)
    covariates: list[str]
    nobs: int
    countries: list[str]
    dropped_countries: list[str]
    deviance: float
    null_deviance: float
    pseudo_r2: float
    converged: bool
    mu: np.ndarray
    fe: bool
    extra: dict = field(default_factory=dict)

    def table(self) -> pd.DataFrame:
        rows = []
        for v in self.covariates:
            b = self.params[v]
            se = float(np.sqrt(self.cov.loc[v, v]))
            se1 = float(np.sqrt(self.cov_hc1.loc[v, v]))
            z = b / se if se > 0 else np.nan
            rows.append({"model": self.name, "term": v, "coef": b, "se_dyadic": se, "z": z,
                         "p": float(2 * stats.norm.sf(abs(z))) if np.isfinite(z) else np.nan,
                         "ci_lo": b - 1.959964 * se, "ci_hi": b + 1.959964 * se, "se_hc1": se1,
                         "nobs": self.nobs, "pseudo_r2": self.pseudo_r2, "deviance": self.deviance})
        return pd.DataFrame(rows)


def fe_matrix(a: np.ndarray, b: np.ndarray, countries: list[str]) -> np.ndarray:
    idx = {c: i for i, c in enumerate(countries)}
    A = np.zeros((len(a), len(countries)))
    A[np.arange(len(a)), [idx[x] for x in a]] = 1.0
    A[np.arange(len(b)), [idx[x] for x in b]] = 1.0
    return A


def design(dyads: pd.DataFrame, covariates: list[str], fe: bool, countries: list[str] | None = None):
    if countries is None:
        countries = sorted(set(dyads["a"]) | set(dyads["b"]))
    cols = [np.ones(len(dyads))]
    names = ["const"]
    for v in covariates:
        cols.append(dyads[v].to_numpy(dtype=float))
        names.append(v)
    X = np.column_stack(cols)
    A = fe_matrix(dyads["a"].to_numpy(), dyads["b"].to_numpy(), countries)
    if fe:
        X = np.column_stack([X, A[:, 1:]])  # first country is the reference
        names += [f"fe_{c}" for c in countries[1:]]
    return X, names, A, countries


def drop_all_zero_countries(dyads: pd.DataFrame, y: str) -> tuple[pd.DataFrame, list[str]]:
    """Countries whose outcome is zero in every pair have FE -> -inf (no MLE);
    drop them iteratively (Santos Silva & Tenreyro 2010; Correia et al. 2019)."""
    dropped: list[str] = []
    d = dyads
    while True:
        tot = pd.concat([d[["a", y]].rename(columns={"a": "c"}), d[["b", y]].rename(columns={"b": "c"})]).groupby("c")[y].sum()
        zero = tot[tot <= 0].index.tolist()
        if not zero:
            return d, dropped
        dropped += zero
        d = d[~d["a"].isin(zero) & ~d["b"].isin(zero)]


def fwl_residualize(Xb: np.ndarray, Z: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """Residualize covariates on the nuisance columns Z (intercept + FE) with
    weights mu (Frisch-Waugh-Lovell for the PPML score equations)."""
    ZW = Z * mu[:, None]
    coef = np.linalg.lstsq(ZW.T @ Z, ZW.T @ Xb, rcond=None)[0]
    return Xb - Z @ coef


def dyadic_cov(Xb: np.ndarray, Z: np.ndarray, resid: np.ndarray, mu: np.ndarray, A: np.ndarray) -> tuple[np.ndarray, dict]:
    """Dyadic-robust covariance of the covariate coefficients only.

    The influence function of beta-hat is (X~'WX~)^{-1} x~_d e_d with X~ the
    covariates residualized on intercept + fixed effects. Using it avoids the
    fixed-effect directions, whose cluster score sums are identically zero by
    the first-order conditions (which makes the full-matrix 'meat' indefinite).
    Meat = sum_c S_c S_c' - sum_d s_d s_d'; small-sample factor G/(G-1)."""
    Xt = fwl_residualize(Xb, Z, mu)
    s = Xt * resid[:, None]
    bread = np.linalg.pinv(Xt.T @ (Xt * mu[:, None]))
    S = A.T @ s
    meat = S.T @ S - s.T @ s
    G = A.shape[1]
    meat *= G / (G - 1)
    V = bread @ meat @ bread
    V = 0.5 * (V + V.T)
    w, Q = np.linalg.eigh(V)
    info = {"min_eigenvalue": float(w.min()), "clipped": bool((w < 0).any()), "floored_at_hc1": False}
    if (w < 0).any():
        # Not PSD (possible in small samples): clip negative eigenvalues, then floor
        # each variance at its HC1 value so no SE collapses toward zero. Flagged.
        V = (Q * np.clip(w, 0, None)) @ Q.T
        s1 = Xt * resid[:, None]
        n, k = Xt.shape
        hc1 = np.diag(bread @ (s1.T @ s1) @ bread) * n / max(1, n - k)
        add = np.clip(hc1 - np.diag(V), 0, None)
        if (add > 0).any():
            V = V + np.diag(add)
            info["floored_at_hc1"] = True
    return V, info


def hc1_cov(X: np.ndarray, resid: np.ndarray, mu: np.ndarray) -> np.ndarray:
    s = X * resid[:, None]
    bread = np.linalg.pinv(X.T @ (X * mu[:, None]))
    n, k = X.shape
    return bread @ (s.T @ s) @ bread * n / (n - k)


def usable_covariates(d: pd.DataFrame, covariates: list[str]) -> tuple[list[str], list[str]]:
    """Drop covariates that are constant in the estimation sample (they are
    collinear with the intercept / fixed effects) and report them."""
    keep, drop = [], []
    for v in covariates:
        (keep if d[v].nunique(dropna=True) > 1 else drop).append(v)
    return keep, drop


def fit_ppml(dyads: pd.DataFrame, y: str, covariates: list[str], *, fe: bool = True, name: str = "",
             maxiter: int = 300, tol: float = 1e-10, start_params=None) -> GravityResult:
    d, dropped = drop_all_zero_countries(dyads, y) if fe else (dyads, [])
    covariates, const_cov = usable_covariates(d, list(covariates))
    X, names, A, countries = design(d, covariates, fe)
    rank = np.linalg.matrix_rank(X)
    if rank < X.shape[1]:
        raise ValueError(f"{name}: design matrix rank {rank} < {X.shape[1]} columns after dropping constant covariates {const_cov}")
    yy = d[y].to_numpy(dtype=float)
    model = sm.GLM(yy, X, family=sm.families.Poisson())
    if start_params is None:
        # log-linear OLS start values make IRLS robust to very large counts
        start_params = np.linalg.lstsq(X, np.log(yy + 0.5), rcond=None)[0]
    res = model.fit(method="IRLS", maxiter=maxiter, tol=tol, start_params=start_params)
    if not res.converged:
        res = model.fit(method="IRLS", maxiter=maxiter * 3, tol=tol)
    mu = res.fittedvalues
    resid = yy - mu
    k = len(covariates)
    cov_idx = list(range(1, 1 + k))
    nuis_idx = [0] + list(range(1 + k, X.shape[1]))
    if k:
        Vb, vinfo = dyadic_cov(X[:, cov_idx], X[:, nuis_idx], resid, mu, A)
    else:
        Vb, vinfo = np.zeros((0, 0)), {}
    V1 = hc1_cov(X, resid, mu)
    params = pd.Series(res.params, index=names)
    corr = np.corrcoef(yy, mu)[0, 1] if np.std(mu) > 0 else np.nan
    return GravityResult(name=name, params=params, cov=pd.DataFrame(Vb, index=covariates, columns=covariates),
                         cov_hc1=pd.DataFrame(V1, index=names, columns=names), covariates=covariates,
                         nobs=len(d), countries=countries, dropped_countries=dropped,
                         deviance=float(res.deviance), null_deviance=float(res.null_deviance),
                         pseudo_r2=float(corr ** 2), converged=bool(res.converged), mu=mu, fe=fe,
                         extra={"dyads": d[["a", "b"] + list(covariates)].reset_index(drop=True), "y": yy,
                                "dropped_constant_covariates": const_cov, "dyadic_cov_info": vinfo})


def predict(result: GravityResult, dyads: pd.DataFrame) -> np.ndarray:
    X, names, _, _ = design(dyads, result.covariates, result.fe, result.countries)
    return np.exp(X @ result.params[names].to_numpy())


def poisson_deviance(y: np.ndarray, mu: np.ndarray) -> float:
    y = np.asarray(y, float)
    mu = np.maximum(np.asarray(mu, float), 1e-300)
    term = np.where(y > 0, y * np.log(np.where(y > 0, y, 1.0) / mu), 0.0)
    return float(2 * np.sum(term - (y - mu)))


def cross_validate(dyads: pd.DataFrame, y: str, models: dict[str, list[str]], *, k: int = 10,
                   seed: int = 0, fe: bool = True) -> pd.DataFrame:
    """K-fold CV over dyads; same folds and same evaluation set for all models.

    Test dyads involving a country whose training outcome is all zero are
    excluded from evaluation for every model (its FE is not identified)."""
    rng = np.random.default_rng(seed)
    d = dyads.reset_index(drop=True)
    folds = rng.permutation(len(d)) % k
    rows = []
    for f in range(k):
        train, test = d[folds != f], d[folds == f]
        train_ok, dropped = drop_all_zero_countries(train, y)
        ok_countries = set(train_ok["a"]) | set(train_ok["b"])
        test_eval = test[test["a"].isin(ok_countries) & test["b"].isin(ok_countries)]
        for mname, cov in models.items():
            r = fit_ppml(train_ok, y, cov, fe=fe, name=mname)
            mu = predict(r, test_eval)
            rows.append({"fold": f, "model": mname, "n_test": len(test_eval),
                         "n_excluded": len(test) - len(test_eval),
                         "deviance": poisson_deviance(test_eval[y].to_numpy(), mu),
                         "pseudo_r2": float(np.corrcoef(test_eval[y], mu)[0, 1] ** 2)})
    return pd.DataFrame(rows)


def cv_compare(cv: pd.DataFrame, base: str, alt: str) -> dict:
    """Paired fold-level comparison: relative deviance reduction of alt vs base."""
    p = cv.pivot(index="fold", columns="model", values="deviance")
    rel = (p[base] - p[alt]) / p[base]
    tot = (p[base].sum() - p[alt].sum()) / p[base].sum()
    n = len(rel)
    se = rel.std(ddof=1) / np.sqrt(n)
    tcrit = stats.t.ppf(0.975, n - 1)
    return {"base": base, "alt": alt, "rel_reduction_total": float(tot),
            "rel_reduction_mean": float(rel.mean()), "ci_lo": float(rel.mean() - tcrit * se),
            "ci_hi": float(rel.mean() + tcrit * se), "folds_improved": int((rel > 0).sum()), "folds": n}


def wald_equal(result: GravityResult, v1: str, v2: str) -> dict:
    diff = result.params[v1] - result.params[v2]
    var = result.cov.loc[v1, v1] + result.cov.loc[v2, v2] - 2 * result.cov.loc[v1, v2]
    z = diff / np.sqrt(var) if var > 0 else np.nan
    return {"term1": v1, "term2": v2, "diff": float(diff), "se": float(np.sqrt(var)),
            "z": float(z), "p": float(2 * stats.norm.sf(abs(z))) if np.isfinite(z) else np.nan}


def vif(dyads: pd.DataFrame, covariates: list[str]) -> pd.DataFrame:
    X = dyads[covariates].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(X)), X])
    out = []
    for i, v in enumerate(covariates, start=1):
        others = np.delete(X, i, axis=1)
        beta, *_ = np.linalg.lstsq(others, X[:, i], rcond=None)
        resid = X[:, i] - others @ beta
        r2 = 1 - resid.var() / X[:, i].var() if X[:, i].var() > 0 else np.nan
        out.append({"term": v, "vif": 1 / (1 - r2) if r2 < 1 else np.inf})
    return pd.DataFrame(out)


def jackknife(dyads: pd.DataFrame, y: str, covariates: list[str], terms: list[str], name: str) -> pd.DataFrame:
    """Re-estimate dropping each country in turn (R5)."""
    countries = sorted(set(dyads["a"]) | set(dyads["b"]))
    full = fit_ppml(dyads, y, covariates, name=name)
    rows = []
    for c in countries:
        sub = dyads[(dyads["a"] != c) & (dyads["b"] != c)]
        try:
            r = fit_ppml(sub, y, covariates, name=name, start_params=None)
        except Exception as exc:  # pragma: no cover - record and continue
            rows.append({"dropped": c, "error": repr(exc)})
            continue
        rows.append({"dropped": c, **{t: float(r.params[t]) for t in terms},
                     **{f"delta_{t}": float(r.params[t] - full.params[t]) for t in terms}})
    return pd.DataFrame(rows)


def fit_negbin(dyads: pd.DataFrame, y: str, covariates: list[str], alpha: float, name: str = "") -> pd.DataFrame:
    """R11: NB2 GLM with country FE and fixed dispersion alpha (HC1 SEs)."""
    d, _ = drop_all_zero_countries(dyads, y)
    covariates, _ = usable_covariates(d, list(covariates))
    X, names, _, _ = design(d, covariates, True)
    res = sm.GLM(d[y].to_numpy(float), X, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type="HC1", maxiter=300)
    p = pd.Series(res.params, index=names)
    se = pd.Series(res.bse, index=names)
    return pd.DataFrame([{"model": name, "term": v, "coef": p[v], "se_hc1": se[v], "alpha": alpha} for v in covariates])
