"""Analysis A: do migrant-destination and collaboration-partner profiles align?

For an origin o, the migration profile is row o of the directed migrant-stock
matrix (where o's emigrants live) and the collaboration profile is row o of
the undirected co-authorship matrix (with whom o's researchers publish), both
over the same destination universe (all other countries in the layer node
set). Pairs absent from a source are zeros in the matrices; whether a zero is
"reported zero" or "unreported" is tracked upstream and handled by the
robustness checks.

Statistics
----------
raw:      Spearman rho, top-k overlap, Jensen-Shannon divergence (base 2)
size-adj: JSD of the strength-preserving expectations (what size alone
          implies) and the difference JSD_obs - JSD_size
residual: Spearman rho between margin-adjusted log residuals of the two
          layers (H1), with a destination-permutation p-value
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..networks.build import Layer
from ..networks.nulls import expected


def jsd(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen-Shannon divergence in bits (0 = identical, 1 = disjoint)."""
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    if p.sum() <= 0 or q.sum() <= 0:
        return float("nan")
    p, q = p / p.sum(), q / q.sum()
    m = 0.5 * (p + q)

    def kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def top_k(values: np.ndarray, labels: list[str], k: int) -> list[str]:
    """Labels of the k largest strictly positive values; ties broken by label."""
    order = sorted([(-v, lab) for v, lab in zip(values, labels) if v > 0])
    return [lab for _, lab in order[:k]]


def topk_overlap(a: np.ndarray, b: np.ndarray, labels: list[str], k: int) -> float:
    ta, tb = set(top_k(a, labels, k)), set(top_k(b, labels, k))
    if not ta or not tb:
        return float("nan")
    return len(ta & tb) / k


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(stats.spearmanr(a, b).statistic)


def log_residuals(layer: Layer) -> np.ndarray:
    E = expected(layer.W, layer.directed)
    return np.log((layer.W + 1.0) / (E + 1.0)), E


def origin_alignment(mig: Layer, col: Layer, origin: str, *, ks=(5, 10), rng: np.random.Generator,
                     n_perm: int = 2000, n_boot: int = 1000, R_mig=None, R_col=None,
                     E_mig=None, E_col=None, mig_noise_sd: float = 0.0) -> dict:
    if mig.nodes != col.nodes:
        raise ValueError("layers must share the same ordered node list")
    nodes = mig.nodes
    o = nodes.index(origin)
    dest = [i for i in range(len(nodes)) if i != o]
    labels = [nodes[i] for i in dest]
    m = mig.W[o, dest]
    c = col.W[o, dest]
    out = {"origin": origin, "emigrants": float(m.sum()), "intl_collab": float(c.sum()),
           "n_dest_mig": int((m > 0).sum()), "n_dest_col": int((c > 0).sum()),
           "spearman_raw": spearman(m, c), "jsd_raw": jsd(m, c)}
    for k in ks:
        out[f"top{k}_overlap"] = topk_overlap(m, c, labels, k)
    # share of collaboration going to the origin's top-10 migrant destinations,
    # and share of emigrants living in its top-10 collaboration partners
    t10m, t10c = top_k(m, labels, 10), top_k(c, labels, 10)
    lab_idx = {lab: i for i, lab in enumerate(labels)}
    out["collab_share_in_top10_mig"] = float(c[[lab_idx[x] for x in t10m]].sum() / c.sum()) if c.sum() > 0 and t10m else np.nan
    out["mig_share_in_top10_col"] = float(m[[lab_idx[x] for x in t10c]].sum() / m.sum()) if m.sum() > 0 and t10c else np.nan

    if R_mig is None:
        R_mig, E_mig = log_residuals(mig)
    if R_col is None:
        R_col, E_col = log_residuals(col)
    em, ec = E_mig[o, dest], E_col[o, dest]
    out["jsd_size_only"] = jsd(em, ec)
    out["jsd_excess"] = out["jsd_raw"] - out["jsd_size_only"]
    rm, rc = R_mig[o, dest], R_col[o, dest]
    rho = spearman(rm, rc)
    out["spearman_resid"] = rho
    if n_perm and not np.isnan(rho):
        perm = np.array([spearman(rm, rng.permutation(rc)) for _ in range(n_perm)])
        out["p_perm_resid"] = float((np.sum(np.abs(perm) >= abs(rho)) + 1) / (n_perm + 1))
    else:
        out["p_perm_resid"] = np.nan
    # parametric bootstrap: Poisson resampling of collaboration counts;
    # migrant stocks are published estimates (fixed unless mig_noise_sd > 0)
    if n_boot:
        js, rs = [], []
        for _ in range(n_boot):
            cb = rng.poisson(c).astype(float)
            mb = m * np.exp(rng.normal(0, mig_noise_sd, size=m.shape)) if mig_noise_sd > 0 else m
            js.append(jsd(mb, cb))
            rs.append(spearman(mb, cb))
        out["jsd_raw_lo"], out["jsd_raw_hi"] = np.nanquantile(js, [0.025, 0.975]).tolist()
        out["spearman_raw_lo"], out["spearman_raw_hi"] = np.nanquantile(rs, [0.025, 0.975]).tolist()
    return out


def alignment_table(mig: Layer, col: Layer, origins: list[str], *, seed: int, ks=(5, 10),
                    n_perm: int = 2000, n_boot: int = 1000, mig_noise_sd: float = 0.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    R_mig, E_mig = log_residuals(mig)
    R_col, E_col = log_residuals(col)
    rows = [origin_alignment(mig, col, o, ks=ks, rng=rng, n_perm=n_perm, n_boot=n_boot,
                             R_mig=R_mig, R_col=R_col, E_mig=E_mig, E_col=E_col,
                             mig_noise_sd=mig_noise_sd) for o in origins]
    df = pd.DataFrame(rows)
    if "p_perm_resid" in df and df["p_perm_resid"].notna().any():
        df["q_perm_resid"] = bh_adjust(df["p_perm_resid"].to_numpy())
    return df


def bh_adjust(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (NaNs preserved)."""
    p = np.asarray(p, dtype=float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    n = pv.size
    if n == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adj = np.empty(n)
    adj[order] = np.minimum(ranked, 1.0)
    out[ok] = adj
    return out


def partial_spearman(x, y, z) -> tuple[float, float]:
    """Spearman correlation of x and y controlling for z (rank residualization)."""
    rx, ry, rz = (stats.rankdata(v) for v in (x, y, z))
    Z = np.column_stack([np.ones_like(rz), rz])
    ex = rx - Z @ np.linalg.lstsq(Z, rx, rcond=None)[0]
    ey = ry - Z @ np.linalg.lstsq(Z, ry, rcond=None)[0]
    r = float(np.corrcoef(ex, ey)[0, 1])
    n = len(x)
    t = r * np.sqrt((n - 3) / max(1e-12, 1 - r ** 2))
    p = float(2 * stats.t.sf(abs(t), df=n - 3))
    return r, p


def h1_test(table: pd.DataFrame) -> dict:
    rho = table["spearman_resid"].dropna().to_numpy()
    res = {"n_origins": int(rho.size), "median_rho_resid": float(np.median(rho)) if rho.size else np.nan,
           "iqr_lo": float(np.quantile(rho, 0.25)) if rho.size else np.nan,
           "iqr_hi": float(np.quantile(rho, 0.75)) if rho.size else np.nan}
    if rho.size >= 5:
        w = stats.wilcoxon(rho, alternative="two-sided")
        res.update({"wilcoxon_stat": float(w.statistic), "wilcoxon_p": float(w.pvalue)})
    if "q_perm_resid" in table:
        sig = table[(table["q_perm_resid"] < 0.05)]
        res["share_sig_positive"] = float((sig["spearman_resid"] > 0).sum() / max(1, rho.size))
        res["share_sig_negative"] = float((sig["spearman_resid"] < 0).sum() / max(1, rho.size))
    return res


def h2_test(table: pd.DataFrame, output_col: str = "log_output", control_col: str | None = "hi_income_share") -> dict:
    d = table.dropna(subset=["jsd_raw", output_col])
    r = stats.spearmanr(d["jsd_raw"], d[output_col])
    res = {"n_origins": len(d), "spearman_jsd_output": float(r.statistic), "p": float(r.pvalue)}
    if control_col and control_col in d and d[control_col].notna().all() and len(d) > 5:
        pr, pp = partial_spearman(d["jsd_raw"].to_numpy(), d[output_col].to_numpy(), d[control_col].to_numpy())
        res.update({"partial_spearman": pr, "partial_p": pp})
    return res
