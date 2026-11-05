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


class RowSampler:
    """Draws an origin's collaboration row in whole-paper (full-count) units and
    converts it to the analysed layer's units.

    For full counting the ratio is 1. For fractional counting each pair's
    observed fractional/full ratio is used (the global ratio where the full
    count is 0), so sampling noise is generated at the level of papers, never
    as Poisson noise on fractional totals."""

    def __init__(self, col: Layer, col_full: Layer | None):
        full = col_full.W if col_full is not None else col.W
        if not np.allclose(full, np.round(full)):
            raise ValueError("the full-count layer must be integer-valued")
        self.full = np.round(full).astype(np.int64)
        tot_f, tot = full.sum(), col.W.sum()
        glob = tot / tot_f if tot_f > 0 else 1.0
        self.ratio = np.where(full > 0, np.divide(col.W, full, out=np.zeros_like(col.W), where=full > 0), glob)

    def poisson(self, o: int, dest: list[int], rng) -> np.ndarray:
        return rng.poisson(self.full[o, dest]) * self.ratio[o, dest]

    def nb_null(self, o: int, dest: list[int], E_full_row: np.ndarray, alpha: float | None, rng) -> np.ndarray:
        if alpha and alpha > 0:
            n = 1.0 / alpha
            draw = rng.negative_binomial(n, n / (n + E_full_row))
        else:
            draw = rng.poisson(E_full_row)
        return draw * self.ratio[o, dest]

    def rarefy(self, o: int, dest: list[int], n: int, rng) -> np.ndarray | None:
        colors = self.full[o, dest]
        if colors.sum() < n:
            return None
        return rng.multivariate_hypergeometric(colors, n) * self.ratio[o, dest]


def origin_alignment(mig: Layer, col: Layer, origin: str, *, ks=(5, 10), rng: np.random.Generator,
                     n_perm: int = 2000, n_boot: int = 1000, R_mig=None, R_col=None,
                     E_mig=None, E_col=None, mig_noise_sd: float = 0.0, null_alpha: float | None = None,
                     sampler: RowSampler | None = None, E_full=None, rarefy_n: int | None = None,
                     n_rarefy: int = 200) -> dict:
    if mig.nodes != col.nodes:
        raise ValueError("layers must share the same ordered node list")
    nodes = mig.nodes
    o = nodes.index(origin)
    dest = [i for i in range(len(nodes)) if i != o]
    labels = [nodes[i] for i in dest]
    m = mig.W[o, dest]
    c = col.W[o, dest]
    sampler = sampler or RowSampler(col, None)
    out = {"origin": origin, "emigrants": float(m.sum()), "intl_collab": float(c.sum()),
           "n_dest_mig": int((m > 0).sum()), "n_dest_col": int((c > 0).sum()),
           "spearman_raw": spearman(m, c), "jsd_raw": jsd(m, c)}
    for k in ks:
        out[f"top{k}_overlap"] = topk_overlap(m, c, labels, k)
    t10m, t10c = top_k(m, labels, 10), top_k(c, labels, 10)
    lab_idx = {lab: i for i, lab in enumerate(labels)}
    out["collab_share_in_top10_mig"] = float(c[[lab_idx[x] for x in t10m]].sum() / c.sum()) if c.sum() > 0 and t10m else np.nan
    out["mig_share_in_top10_col"] = float(m[[lab_idx[x] for x in t10c]].sum() / m.sum()) if m.sum() > 0 and t10c else np.nan

    if R_mig is None:
        R_mig, E_mig = log_residuals(mig)
    if R_col is None:
        R_col, E_col = log_residuals(col)
    if E_full is None:
        E_full = E_col
    em, ec = E_mig[o, dest], E_col[o, dest]
    out["jsd_size_only"] = jsd(em, ec)
    out["jsd_excess"] = out["jsd_raw"] - out["jsd_size_only"]
    rm, rc = R_mig[o, dest], R_col[o, dest]
    rho = spearman(rm, rc)
    out["spearman_resid"] = rho
    out["partial_spearman_resid"] = partial_spearman_multi(rm, rc, np.column_stack([np.log1p(em), np.log1p(ec)]))
    if n_perm and not np.isnan(rho):
        # (i) destination-label permutation (NOT size-calibrated; reported for reference)
        perm = np.array([spearman(rm, rng.permutation(rc)) for _ in range(n_perm)])
        out["p_perm_resid"] = float((np.sum(np.abs(perm) >= abs(rho)) + 1) / (n_perm + 1))
        # (ii) size-preserving simulation null (primary, plan v1.1): collaboration
        # papers drawn from NB2(E_full, alpha) around the independence expectation of
        # the full-count layer (alpha = its ML dispersion around that expectation),
        # converted to the analysed layer's units; migration held fixed. Zero cells
        # give residuals -ln(1+E) that fall with destination size in both layers, so
        # rho > 0 arises without shared affinity; this null reproduces that artefact.
        efr = E_full[o, dest]
        sims = np.array([spearman(rm, np.log((sampler.nb_null(o, dest, efr, null_alpha, rng) + 1.0) / (ec + 1.0)))
                         for _ in range(n_perm)])
        sims = sims[~np.isnan(sims)]
        out["rho_null_mean"] = float(sims.mean()) if sims.size else np.nan
        out["rho_excess"] = rho - out["rho_null_mean"]
        out["p_sim_resid"] = float((np.sum(np.abs(sims - sims.mean()) >= abs(rho - sims.mean())) + 1) / (sims.size + 1)) if sims.size else np.nan
    else:
        out["p_perm_resid"] = out["p_sim_resid"] = out["rho_null_mean"] = out["rho_excess"] = np.nan
    # Plug-in JSD is biased upward for sparse rows, and the bias shrinks with the
    # number of papers (i.e. with capacity). Two corrections (plan v1.2):
    #  * rarefied JSD: mean JSD after subsampling every origin to the same number
    #    of paper-pair incidences (used for H2, which compares origins);
    #  * bias-corrected JSD with a basic-bootstrap interval (paper-level resampling).
    if rarefy_n:
        vals = [jsd(m, x) for x in (sampler.rarefy(o, dest, rarefy_n, rng) for _ in range(n_rarefy)) if x is not None]
        out["jsd_rarefied"] = float(np.mean(vals)) if vals else np.nan
        out["rarefy_n"] = rarefy_n
    if n_boot:
        js, rs = [], []
        for _ in range(n_boot):
            cb = sampler.poisson(o, dest, rng)
            mb = m * np.exp(rng.normal(0, mig_noise_sd, size=m.shape)) if mig_noise_sd > 0 else m
            js.append(jsd(mb, cb))
            rs.append(spearman(mb, cb))
        js, rs = np.array(js), np.array(rs)
        j = out["jsd_raw"]
        out["jsd_bc"] = float(2 * j - np.nanmean(js))
        q_lo, q_hi = np.nanquantile(js, [0.025, 0.975])
        out["jsd_bc_lo"], out["jsd_bc_hi"] = float(2 * j - q_hi), float(2 * j - q_lo)
        r = out["spearman_raw"]
        s_lo, s_hi = np.nanquantile(rs, [0.025, 0.975])
        out["spearman_raw_lo"], out["spearman_raw_hi"] = float(2 * r - s_hi), float(2 * r - s_lo)
    return out


def alignment_table(mig: Layer, col: Layer, origins: list[str], *, seed: int, ks=(5, 10),
                    n_perm: int = 2000, n_boot: int = 1000, mig_noise_sd: float = 0.0,
                    col_full: Layer | None = None, rarefy_n: int | None = None) -> pd.DataFrame:
    """Per-origin alignment statistics. ``col_full`` is the full-count layer when
    ``col`` is fractional (needed for paper-level sampling and the NB null)."""
    rng = np.random.default_rng(seed)
    R_mig, E_mig = log_residuals(mig)
    R_col, E_col = log_residuals(col)
    full = col_full if col_full is not None else col
    sampler = RowSampler(col, col_full)
    E_full = E_col if col_full is None else log_residuals(col_full)[1]
    from .residuals import nb2_alpha
    iu = np.triu_indices(len(col.nodes), 1)
    null_alpha = nb2_alpha(full.W[iu], E_full[iu]) if n_perm else None
    rows = [origin_alignment(mig, col, o, ks=ks, rng=rng, n_perm=n_perm, n_boot=n_boot,
                             R_mig=R_mig, R_col=R_col, E_mig=E_mig, E_col=E_col,
                             mig_noise_sd=mig_noise_sd, null_alpha=null_alpha, sampler=sampler,
                             E_full=E_full, rarefy_n=rarefy_n) for o in origins]
    df = pd.DataFrame(rows)
    df["null_alpha"] = null_alpha
    if "p_perm_resid" in df and df["p_perm_resid"].notna().any():
        df["q_perm_resid"] = bh_adjust(df["p_perm_resid"].to_numpy())
    if "p_sim_resid" in df and df["p_sim_resid"].notna().any():
        df["q_sim_resid"] = bh_adjust(df["p_sim_resid"].to_numpy())
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


def partial_spearman_multi(x, y, Z) -> float:
    """Spearman correlation of x and y after rank-residualizing both on the
    columns of Z (sensitivity statistic for H1)."""
    rx, ry = stats.rankdata(x), stats.rankdata(y)
    RZ = np.column_stack([np.ones(len(rx))] + [stats.rankdata(z) for z in np.atleast_2d(Z.T)])
    ex = rx - RZ @ np.linalg.lstsq(RZ, rx, rcond=None)[0]
    ey = ry - RZ @ np.linalg.lstsq(RZ, ry, rcond=None)[0]
    if ex.std() == 0 or ey.std() == 0:
        return float("nan")
    return float(np.corrcoef(ex, ey)[0, 1])


def h1_test(table: pd.DataFrame) -> dict:
    """H1 (plan v1.1): the median *excess* residual alignment (observed rho minus
    the size-preserving simulation null mean) is tested against 0 (Wilcoxon);
    per-origin significance uses the simulation p-values with BH. The raw
    residual rho and the permutation p-values are reported for reference."""
    rho = table["spearman_resid"].dropna().to_numpy()
    ex = table["rho_excess"].dropna().to_numpy() if "rho_excess" in table else np.array([])
    res = {"n_origins": int(rho.size), "median_rho_resid": float(np.median(rho)) if rho.size else np.nan,
           "iqr_lo": float(np.quantile(rho, 0.25)) if rho.size else np.nan,
           "iqr_hi": float(np.quantile(rho, 0.75)) if rho.size else np.nan,
           "median_rho_excess": float(np.median(ex)) if ex.size else np.nan,
           "median_rho_null": float(table["rho_null_mean"].median()) if "rho_null_mean" in table else np.nan}
    if ex.size >= 5:
        w = stats.wilcoxon(ex, alternative="two-sided")
        res.update({"wilcoxon_stat": float(w.statistic), "wilcoxon_p": float(w.pvalue)})
    if "q_sim_resid" in table:
        sig = table[(table["q_sim_resid"] < 0.05)]
        res["share_sig_positive"] = float((sig["rho_excess"] > 0).sum() / max(1, ex.size))
        res["share_sig_negative"] = float((sig["rho_excess"] < 0).sum() / max(1, ex.size))
    if "q_perm_resid" in table:
        res["share_sig_perm_reference"] = float((table["q_perm_resid"] < 0.05).sum() / max(1, rho.size))
    return res


def h2_test(table: pd.DataFrame, output_col: str = "log_output", control_col: str | None = "hi_income_share",
            jsd_col: str = "jsd_rarefied") -> dict:
    """H2 (plan v1.2): the divergence measure is the *rarefied* JSD, so that
    origins with more papers are not mechanically less divergent. The plug-in
    JSD version is reported for reference."""
    if jsd_col not in table:
        jsd_col = "jsd_raw"
    d = table.dropna(subset=[jsd_col, output_col])
    r = stats.spearmanr(d[jsd_col], d[output_col])
    res = {"n_origins": len(d), "jsd_measure": jsd_col, "spearman_jsd_output": float(r.statistic), "p": float(r.pvalue)}
    if jsd_col != "jsd_raw":
        dr = table.dropna(subset=["jsd_raw", output_col])
        rr = stats.spearmanr(dr["jsd_raw"], dr[output_col])
        res.update({"reference_plugin_spearman": float(rr.statistic), "reference_plugin_p": float(rr.pvalue)})
    if control_col and control_col in d and d[control_col].notna().all() and len(d) > 5:
        pr, pp = partial_spearman(d[jsd_col].to_numpy(), d[output_col].to_numpy(), d[control_col].to_numpy())
        res.update({"partial_spearman": pr, "partial_p": pp})
    return res
