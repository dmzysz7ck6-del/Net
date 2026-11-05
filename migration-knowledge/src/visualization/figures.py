"""Publication figures. Every figure is computed from pipeline outputs; no
hand-entered values. Measured values, model predictions and uncertainty are
visually distinct (filled marks = measured; hollow/lines = model; bands =
uncertainty)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch

from ..cleaning import countries as C
from ..networks.build import Layer
from . import style as S


def _shares(layer: Layer, origin: str) -> pd.Series:
    i = layer.index[origin]
    row = layer.W[i].astype(float)
    s = row.sum()
    return pd.Series(row / s if s > 0 else row, index=layer.nodes).drop(origin)


# ---------------------------------------------------------------- Figure 1
def subset_rule(layers: dict[str, Layer], focus: list[str], n_partners: int = 8) -> list[str]:
    """Fixed subset: focus origins plus the n_partners countries receiving the
    largest average share of the focus origins' ties across the three layers
    (each layer row-normalized so no layer dominates by scale)."""
    nodes = layers["migration"].nodes
    focus = [f for f in focus if f in nodes]
    score = pd.Series(0.0, index=nodes)
    for L in layers.values():
        for f in focus:
            score = score.add(_shares(L, f), fill_value=0)
    score = score.drop(focus, errors="ignore").sort_values(ascending=False)
    return focus + score.head(n_partners).index.tolist()


def _region_order(iso3: str) -> tuple:
    cw = C.crosswalk().set_index("iso3")
    cont = cw.loc[iso3, "continent"] if iso3 in cw.index else "ZZ"
    rank = {"Africa": 0, "Asia": 2, "Europe": 1, "America": 3, "Oceania": 4}.get(cont, 5)
    return (rank, cw.loc[iso3, "subregion"] if iso3 in cw.index else "", iso3)


def figure1_three_networks(layers: dict[str, Layer], coords: pd.DataFrame | None, focus: list[str], out_dir: Path,
                           window_label: str, min_share: float = 0.03,
                           title: str = "Migration, scholarly mobility and co-authorship from ten Sub-Saharan origins") -> list[Path]:
    """Bipartite small multiples with identical node positions in every panel:
    focus origins on the left, destinations (the fixed subset, grouped by
    continent and UN subregion) on the right."""
    S.apply()
    subset = subset_rule(layers, focus)
    origins = sorted([f for f in focus if f in layers["migration"].index], key=_region_order)
    dests = sorted(subset, key=_region_order)
    yo = {o: 1 - i / max(1, len(origins) - 1) for i, o in enumerate(origins)}
    yd = {d: 1 - i / max(1, len(dests) - 1) for i, d in enumerate(dests)}
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 7.2))
    titles = {"migration": "Migrant stock\n(people born in origin, living in destination)",
              "scholars": "Scholarly moves\n(affiliation changes, origin → destination)",
              "collaboration": "Co-authored articles\n(undirected, full counting)"}
    for ax, (key, L) in zip(axes, layers.items()):
        ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        color = S.LAYER[key]
        for o in origins:
            sh = _shares(L, o)
            for d in dests:
                v = sh.get(d, 0.0)
                if d == o or v < min_share:
                    continue
                arrow = FancyArrowPatch((0.08, yo[o]), (0.92, yd[d]), connectionstyle="arc3,rad=0.0",
                                        arrowstyle="-", lw=0.3 + 9 * v, color=color, alpha=0.55, zorder=2)
                ax.add_patch(arrow)
        for o in origins:
            ax.scatter([0.08], [yo[o]], s=28, color=S.INK, zorder=3)
            ax.text(0.05, yo[o], C.name(o), ha="right", va="center", fontsize=8, color=S.INK)
        for d in dests:
            filled = d in focus
            ax.scatter([0.92], [yd[d]], s=28, zorder=3, facecolor=S.INK if filled else S.SURFACE, edgecolor=S.INK, linewidth=1)
            ax.text(0.95, yd[d], C.name(d), ha="left", va="center", fontsize=8, color=S.INK2)
        ax.set_xlim(-0.32, 1.32); ax.set_ylim(-0.05, 1.05)
        ax.set_title(titles.get(key, key), loc="center", color=S.INK, fontsize=10)
    S.headline(fig, title, f"Each origin's ties to a fixed set of destinations, by layer · {window_label}")
    S.footnote(fig, "Left: ten focus origins. Right: the focus origins plus the eight countries holding the largest average share of their ties across the "
                    f"three layers (fixed rule), grouped by continent. Line width = share of the origin's total in that layer (shown if ≥ {min_share:.0%}), "
                    "so widths are comparable across panels. Migration and mobility are directed origin → destination; co-authorship is undirected. "
                    "All values measured, none modelled.\n" + S.SOURCE_NOTE)
    fig.subplots_adjust(top=0.86, bottom=0.1, wspace=0.15, left=0.02, right=0.98)
    return S.save(fig, out_dir, "fig1_three_networks")


# ---------------------------------------------------------------- Figure 2
def divergence_matrix(mig: Layer, col: Layer, origins: list[str], n_dest: int = 15) -> pd.DataFrame:
    """Percentage-point difference between an origin's collaboration-partner
    share and its migrant-destination share, for the destinations most
    important to the listed origins in either layer."""
    rows, imp = {}, pd.Series(0.0, index=mig.nodes)
    for o in origins:
        p, q = _shares(mig, o), _shares(col, o)
        rows[o] = (q - p) * 100
        imp = imp.add(p.abs() + q.abs(), fill_value=0)
    dest = imp.drop(origins, errors="ignore").sort_values(ascending=False).head(n_dest).index
    return pd.DataFrame(rows).T.reindex(columns=dest)


def figure2_divergence(mat: pd.DataFrame, out_dir: Path, window_label: str, jsd: pd.Series | None = None,
                       title: str = "Where collaboration and diaspora shares differ") -> list[Path]:
    S.apply()
    if jsd is not None:
        mat = mat.loc[jsd.reindex(mat.index).sort_values().index]
    vmax = np.nanmax(np.abs(mat.to_numpy())) if mat.size else 1
    fig, ax = plt.subplots(figsize=(11, 0.42 * len(mat) + 2.6))
    im = ax.imshow(mat.to_numpy(), cmap=S.DIVERGING, vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(mat.shape[1]), mat.columns, rotation=0, fontsize=8)
    ax.set_yticks(range(mat.shape[0]), [f"{C.name(o)}" + (f"  (JSD {jsd[o]:.2f})" if jsd is not None and o in jsd and np.isfinite(jsd[o]) else "") for o in mat.index], fontsize=8.5)
    ax.grid(False)
    ax.set_xticks(np.arange(-.5, mat.shape[1]), minor=True); ax.set_yticks(np.arange(-.5, mat.shape[0]), minor=True)
    ax.grid(which="minor", color=S.SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for (i, j), v in np.ndenumerate(mat.to_numpy()):
        if np.isfinite(v) and abs(v) >= 0.35 * vmax:
            ax.text(j, i, f"{v:+.0f}", ha="center", va="center", fontsize=7, color="#ffffff" if abs(v) > 0.6 * vmax else S.INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.set_label("collaboration share − migrant share (percentage points)", color=S.INK2)
    cb.outline.set_visible(False)
    S.headline(fig, title,
               f"Red: destination hosts more of the origin's emigrants than of its co-authored papers; blue: the reverse · {window_label}")
    S.footnote(fig, "Shares are computed over the common country universe (measured, full counting). Rows sorted by Jensen–Shannon divergence "
                    "between the two distributions, rarefied to 50 paper-pair incidences so that origins with more papers are not mechanically ranked as less divergent. "
                    "Columns: destinations most important to these origins in either layer.\n" + S.SOURCE_NOTE)
    fig.subplots_adjust(top=0.86, bottom=0.12)
    return S.save(fig, out_dir, "fig2_divergence_heatmap")


# ---------------------------------------------------------------- Figure 3
def figure3_expected_observed(res: pd.DataFrame, out_dir: Path, window_label: str, highlight: list[str],
                              n_labels: int = 12, title: str = "Observed versus model-expected co-authorship") -> list[Path]:
    S.apply()
    d = res.copy()
    fig, ax = plt.subplots(figsize=(8.2, 7.6))
    x = d["expected"] + 1
    y = d["observed"] + 1
    ctx = ~d["category"].isin(["stronger_than_expected", "weaker_than_expected"])
    ax.scatter(x[ctx], y[ctx], s=6, color=S.CONTEXT, alpha=0.5, lw=0, label="within expectation or not testable")
    for cat, col, lab in [("stronger_than_expected", S.STRONGER, "stronger than expected (q < 0.05, ≥2×)"),
                          ("weaker_than_expected", S.WEAKER, "weaker than expected (q < 0.05, ≤½×)")]:
        m = d["category"] == cat
        ax.scatter(x[m], y[m], s=16, color=col, edgecolor=S.SURFACE, linewidth=0.6, label=f"{lab}: {int(m.sum())} pairs", zorder=3)
    # NB2 95% predictive band as a function of the expected count (model)
    alpha = float(d["nb_alpha"].iloc[0]) if "nb_alpha" in d else 0.0
    grid = np.logspace(0, np.log10(max(10, x.max())), 200)
    from scipy import stats
    mu = grid - 1
    n = 1 / alpha if alpha > 0 else 1e9
    lo = stats.nbinom.ppf(0.025, n, n / (n + np.maximum(mu, 1e-9))) + 1
    hi = stats.nbinom.ppf(0.975, n, n / (n + np.maximum(mu, 1e-9))) + 1
    ax.fill_between(grid, lo, hi, color=S.SEQ_BLUE[0], alpha=0.6, lw=0, label="95% predictive range (NB2, model)", zorder=1)
    ax.plot(grid, grid, color=S.INK2, lw=1, label="observed = expected", zorder=2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Expected co-authored articles, model M2 (+1, log scale)")
    ax.set_ylabel("Observed co-authored articles (+1, log scale)")
    flagged = d[~ctx].copy()
    flagged["inv"] = flagged["a"].isin(highlight) | flagged["b"].isin(highlight)
    lab = flagged[flagged["inv"]].reindex(flagged[flagged["inv"]]["pearson_resid_nb"].abs().sort_values(ascending=False).index).head(n_labels)
    for r in lab.itertuples():
        ax.annotate(f"{r.a}–{r.b}", (r.expected + 1, r.observed + 1), xytext=(4, -2), textcoords="offset points",
                    fontsize=7.2, color=S.INK)
    ax.legend(loc="upper left", fontsize=7.8)
    S.headline(fig, title,
               f"Observed vs. expected co-authorship for every country pair · {window_label}")
    S.footnote(fig, "Expected values from PPML model M2 (country fixed effects, distance, contiguity, language, colonial ties, migrant stock). "
                    "Flags: negative-binomial predictive test with parameter uncertainty, Benjamini–Hochberg q < 0.05, expected ≥ 5, "
                    "|log ratio| ≥ ln 2. Labelled: largest flagged deviations involving the ten focus origins.\n" + S.SOURCE_NOTE)
    fig.subplots_adjust(top=0.88, bottom=0.14)
    return S.save(fig, out_dir, "fig3_expected_vs_observed")


# ---------------------------------------------------------------- Figure 4
def figure4_case(layers: dict[str, Layer], res: pd.DataFrame, origins: list[str], out_dir: Path, window_label: str,
                 n_dest: int = 10, title: str | None = None) -> list[Path]:
    S.apply()
    fig, axes = plt.subplots(1, len(origins), figsize=(6.2 * len(origins), 5.6), squeeze=False)
    for ax, o in zip(axes[0], origins):
        p = _shares(layers["migration"], o)
        q = _shares(layers["collaboration"], o)
        r = _shares(layers["scholars"], o) if "scholars" in layers else None
        dest = (p + q).sort_values(ascending=False).head(n_dest).index[::-1]
        sub = res[(res["a"] == o) | (res["b"] == o)].copy()
        sub["partner"] = np.where(sub["a"] == o, sub["b"], sub["a"])
        exp = sub.set_index("partner")["expected"]
        exp_share = exp / sub["observed"].sum() if sub["observed"].sum() > 0 else exp * 0
        yy = np.arange(len(dest))
        h = 0.26
        ax.barh(yy + h, p.reindex(dest) * 100, height=h, color=S.LAYER["migration"], label="share of emigrants (measured)")
        ax.barh(yy, q.reindex(dest) * 100, height=h, color=S.LAYER["collaboration"], label="share of co-authored articles (measured)")
        if r is not None:
            ax.barh(yy - h, r.reindex(dest) * 100, height=h, color=S.LAYER["scholars"], label="share of scholarly moves out (measured)")
        ax.scatter(exp_share.reindex(dest) * 100, yy, marker="|", s=160, color=S.INK, zorder=4, label="expected article share, model M2")
        ax.set_yticks(yy, [C.name(x) for x in dest], fontsize=8.5)
        ax.set_xlabel("% of origin's total in each layer")
        ax.set_title(C.name(o), loc="left")
        ax.grid(axis="y", visible=False)
    axes[0][0].legend(loc="lower right", fontsize=7.6)
    S.headline(fig, title or "Diaspora destinations and research partners, side by side",
               f"Top destinations by combined share · {window_label}")
    S.footnote(fig, "Bars are measured shares; the black tick is the model-expected share of the origin's co-authored articles "
                    "(PPML M2, which already includes migrant stock). Scholarly moves are origin→destination affiliation changes, 2010–14.\n" + S.SOURCE_NOTE)
    fig.subplots_adjust(top=0.85, bottom=0.15, wspace=0.45)
    return S.save(fig, out_dir, "fig4_case_study")


# ---------------------------------------------------------------- Figure 5
def figure5_temporal(align: dict[str, pd.DataFrame], gravity: dict[str, pd.DataFrame], focus: list[str],
                     out_dir: Path, title: str = "Alignment between the layers across three windows") -> list[Path]:
    S.apply()
    order = [w for w in ["earlier", "primary", "later"] if w in align]
    labels = {"earlier": "2010 stock\n2010–14 papers", "primary": "2015 stock\n2015–19 papers", "later": "2020 stock\n2020–24 papers"}
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8))
    ax = axes[0]
    data = [align[w]["spearman_resid"].dropna() for w in order]
    ax.boxplot(data, widths=0.45, showfliers=False, medianprops={"color": S.INK}, boxprops={"color": S.INK2},
               whiskerprops={"color": S.INK2}, capprops={"color": S.INK2})
    ax.set_xticks(range(1, len(order) + 1), [labels[w] for w in order], fontsize=8)
    ax.axhline(0, color=S.AXIS, lw=0.8)
    ax.set_title("Size-adjusted alignment, all origins", loc="left")
    ax.set_ylabel("Spearman ρ of residual profiles")
    ax = axes[1]
    jcol = "jsd_rarefied" if all("jsd_rarefied" in align[w] for w in order) else "jsd_raw"
    for f in focus:
        vals = [align[w].set_index("origin")[jcol].get(f, np.nan) for w in order]
        if np.all(np.isnan(vals)):
            continue
        ax.plot(range(1, len(order) + 1), vals, color=S.LAYER["migration"], lw=1.2, marker="o", ms=4, alpha=0.8)
        ax.annotate(f, (len(order), vals[-1]), xytext=(4, 0), textcoords="offset points", fontsize=7, color=S.INK2, va="center")
    ax.set_xticks(range(1, len(order) + 1), [labels[w] for w in order], fontsize=8)
    ax.set_title("Divergence for the ten focus origins", loc="left")
    ax.set_ylabel("Jensen–Shannon divergence, rarefied (0 = identical)" if jcol == "jsd_rarefied" else "Jensen–Shannon divergence (0 = identical)")
    ax = axes[2]
    for k, (term, col, lab) in enumerate([("ln_mig", S.LAYER["migration"], "migrant stock (M3)"),
                                          ("ln_mob", S.LAYER["scholars"], "scholarly moves (M3)")]):
        xs, ys, lo, hi = [], [], [], []
        for i, w in enumerate(order):
            g = gravity.get(w)
            if g is None:
                continue
            r = g[(g["model"] == "M3") & (g["term"] == term)]
            if len(r):
                xs.append(i + 1 + (k - 0.5) * 0.18); ys.append(r["coef"].iloc[0]); lo.append(r["ci_lo"].iloc[0]); hi.append(r["ci_hi"].iloc[0])
        ax.errorbar(xs, ys, yerr=[np.array(ys) - np.array(lo), np.array(hi) - np.array(ys)], fmt="o", color=col,
                    ecolor=col, elinewidth=1.4, capsize=0, ms=5, label=lab)
    ax.axhline(0, color=S.AXIS, lw=0.8)
    ax.set_xticks(range(1, len(order) + 1), [labels[w] for w in order], fontsize=8)
    ax.set_title("Gravity coefficients (95% CI, dyadic-robust)", loc="left")
    ax.set_ylabel("PPML coefficient on ln(1 + x)")
    ax.legend(fontsize=7.8, loc="best")
    S.headline(fig, title,
               "Each window pairs a stock year with the preceding five years of scholarly moves and the following five years of papers")
    S.footnote(fig, "Three windows of one UN DESA revision (2024). Three points describe change; they do not identify a trend. "
                    "Scholarly mobility windows: 2005–09, 2010–14, 2015–19.\n" + S.SOURCE_NOTE)
    fig.subplots_adjust(top=0.82, bottom=0.2, wspace=0.32)
    return S.save(fig, out_dir, "fig5_over_time")


# ---------------------------------------------------------------- Figure 6
def figure6_coefficients(grav: pd.DataFrame, cv: list[dict], out_dir: Path, window_label: str,
                         title: str = "What migration and scholarly mobility add to a gravity model of co-authorship") -> list[Path]:
    S.apply()
    terms = ["ln_distw", "contig", "comlang_off", "colony", "comcol", "ln_mig", "ln_mob"]
    names = {"ln_distw": "ln distance", "contig": "contiguity", "comlang_off": "common official language",
             "colony": "colonial link", "comcol": "common colonizer", "ln_mig": "ln(1 + migrant stock)",
             "ln_mob": "ln(1 + scholarly moves)"}
    models = ["M1", "M2", "M3"]
    cols = {"M1": S.MUTED, "M2": S.LAYER["migration"], "M3": S.LAYER["scholars"]}
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1.6, 1]})
    for k, m in enumerate(models):
        g = grav[grav["model"] == m].set_index("term")
        yy = [i + (k - 1) * 0.22 for i, t in enumerate(terms) if t in g.index]
        tt = [t for t in terms if t in g.index]
        ax.errorbar(g.loc[tt, "coef"], yy, xerr=[g.loc[tt, "coef"] - g.loc[tt, "ci_lo"], g.loc[tt, "ci_hi"] - g.loc[tt, "coef"]],
                    fmt="o", color=cols[m], ms=4.5, elinewidth=1.3, capsize=0, label=m)
    ax.axvline(0, color=S.AXIS, lw=0.8)
    ax.set_yticks(range(len(terms)), [names[t] for t in terms])
    ax.invert_yaxis()
    ax.set_xlabel("PPML coefficient (95% CI, dyadic-robust)")
    ax.legend(title=None, fontsize=8, loc="lower right")
    ax.set_title("Coefficients", loc="left")
    labels = [f"{c['alt']} vs {c['base']}" for c in cv]
    vals = [100 * c["rel_reduction_mean"] for c in cv]
    lo = [100 * c["ci_lo"] for c in cv]
    hi = [100 * c["ci_hi"] for c in cv]
    yy = np.arange(len(cv))
    ax2.errorbar(vals, yy, xerr=[np.array(vals) - np.array(lo), np.array(hi) - np.array(vals)], fmt="o",
                 color=S.INK, ms=5, elinewidth=1.3, capsize=0)
    ax2.axvline(0, color=S.AXIS, lw=0.8)
    ax2.set_yticks(yy, labels)
    ax2.invert_yaxis()
    ax2.set_xlabel("Out-of-fold deviance reduction (%, 10-fold CV, 95% CI)")
    ax2.set_title("Predictive gain", loc="left")
    S.headline(fig, title,
               f"M1: country fixed effects + geography, language, colonial ties · M2: + migrant stock · M3: + scholarly moves · {window_label}")
    S.footnote(fig, "Model estimates, not causal effects. Country fixed effects absorb research output, GDP and population.\n" + S.SOURCE_NOTE)
    fig.subplots_adjust(top=0.84, bottom=0.16, wspace=0.55)
    return S.save(fig, out_dir, "fig6_gravity_coefficients")
