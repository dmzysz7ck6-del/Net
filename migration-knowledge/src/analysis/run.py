"""Run all pre-registered analyses for one design window.

Reads the processed data contract (``data/processed``), writes every table
used by the report to ``outputs/tables`` and model objects to
``outputs/models``. Nothing in this module reads raw files or the network.

Processed inputs
----------------
migration_stocks.csv  origin_iso3, dest_iso3, year, stock, dest_data_type, corridor_status
scholarly_moves.csv   origin_iso3, dest_iso3, year, moves, source ('openalex' | 'scopus')
collab_<y0>_<y1>.csv  a, b, full, frac, full_nomega, frac_nomega
output_<y0>_<y1>.csv  iso3, articles, intl_articles
wdi_panel.csv         iso3, year, population, gdp_pc_ppp_const, income_id, ...
geo_dyads.csv         a, b, distw, dist, contig, comlang_off, comlang_ethno, colony, comcol, geo_imputed
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..cleaning import countries as C
from ..cleaning import panel as P
from ..config import PATHS, load_config, seed as cfg_seed, window as get_window
from ..networks.build import Layer, directed_layer, undirected_layer
from . import alignment as A
from . import gravity as G
from . import residuals as R
from . import topology as T

BASE = ["ln_distw", "contig", "comlang_off", "colony", "comcol"]
MODELS = {
    "M1": BASE,
    "M2": BASE + ["ln_mig"],
    "M3": BASE + ["ln_mig", "ln_mob"],
    "M1_mob": BASE + ["ln_mob"],
    "M3_dir": BASE + ["ln_mig", "ln_mob_up", "ln_mob_down"],
    "M3_dir_both": BASE + ["ln_mig_up", "ln_mig_down", "ln_mob_up", "ln_mob_down"],
}


@dataclass
class WindowData:
    name: str
    window: dict
    universe: pd.DataFrame
    nodes: list[str]
    dyads: pd.DataFrame
    migration: pd.DataFrame
    mobility: pd.DataFrame
    mobility_all: pd.DataFrame
    collab: pd.DataFrame
    output: pd.DataFrame
    wdi: pd.DataFrame
    dest_types: pd.Series
    intl_articles: pd.Series


def _read(name: str) -> pd.DataFrame:
    path = PATHS.processed / name
    if not path.exists():
        raise FileNotFoundError(f"missing processed input {path}; run `make clean-data` first")
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def load_window(name: str, *, min_population: float | None = None, mobility_source: str = "openalex",
                collab_col: str = "full") -> WindowData:
    cfg = load_config()
    w = get_window(name)
    min_population = cfg["countries"]["min_population"] if min_population is None else min_population
    mig_all = _read("migration_stocks.csv")
    mig = mig_all[mig_all["year"] == w["migrant_stock_year"]].copy()
    mob_all = _read("scholarly_moves.csv")
    lo, hi = w["mobility_years"]
    mob_src = mob_all[mob_all["source"] == mobility_source]
    mob = mob_src[(mob_src["year"] >= lo) & (mob_src["year"] <= hi)].copy()
    cy = tuple(w["collab_years"])
    col = _read(f"collab_{cy[0]}_{cy[1]}.csv")
    capy = tuple(w["capacity_years"])
    out = _read(f"output_{capy[0]}_{capy[1]}.csv")
    wdi = _read("wdi_panel.csv")
    geo = _read("geo_dyads.csv")
    P.check_alignment(w, mig, mob, cy)

    sources = {
        "undesa": set(mig["origin_iso3"]) | set(mig["dest_iso3"]),
        "openalex": set(col["a"]) | set(col["b"]),
        "cepii": set(geo["a"]) | set(geo["b"]),
    }
    candidates = sorted(set.union(*sources.values()))
    uni = P.select_universe(candidates, wdi, col.rename(columns={collab_col: "full"}) if collab_col != "full" else col,
                            w, min_population, sources,
                            wdi_absent_allowlist=tuple(cfg["countries"].get("wdi_absent_allowlist", [])))
    nodes = uni.loc[uni["included"], "iso3"].tolist()
    dyads = P.build_dyads(nodes, mig, mob, col, geo, out,
                          collab_cols=[c for c in ["full", "frac", "full_nomega", "frac_nomega"] if c in col])
    # Scopus mobility as a robustness variable when available
    mob_sc = mob_all[(mob_all["source"] == "scopus") & (mob_all["year"] >= lo) & (mob_all["year"] <= hi)]
    if len(mob_sc):
        sc = mob_sc.groupby(["origin_iso3", "dest_iso3"])["moves"].sum()
        ab = sc.reindex(pd.MultiIndex.from_frame(dyads[["a", "b"]])).fillna(0).to_numpy()
        ba = sc.reindex(pd.MultiIndex.from_frame(dyads[["b", "a"]])).fillna(0).to_numpy()
        dyads["ln_mob_scopus"] = np.log1p(ab + ba)
    problems = P.validate_dyads(dyads)
    if problems:
        raise ValueError(f"dyad integrity problems in window {name}: {problems}")
    PATHS.ensure()
    P.missing_geography(dyads).to_csv(PATHS.tables / f"missing_geography_{name}.csv", index=False)
    types = mig.drop_duplicates("dest_iso3").set_index("dest_iso3")["dest_data_type"]
    intl = _read(f"collab_{cy[0]}_{cy[1]}_nodes.csv").set_index("iso3")["intl_articles"]
    return WindowData(name, w, uni, nodes, dyads, mig, mob, mob_all, col, out, wdi, types, intl)


def layers(wd: WindowData, collab_col: str = "full") -> dict[str, Layer]:
    mig = directed_layer(wd.migration.fillna({"stock": 0}), wd.nodes, "origin_iso3", "dest_iso3", "stock",
                         "migration", "persons")
    mob = directed_layer(wd.mobility, wd.nodes, "origin_iso3", "dest_iso3", "moves", "scholars", "moves")
    col = undirected_layer(wd.collab, wd.nodes, "a", "b", collab_col, f"collaboration_{collab_col}", "works")
    return {"migration": mig, "scholars": mob, "collaboration": col}


def comparison_origins(wd: WindowData, focus: list[str], per_origin: int) -> pd.DataFrame:
    year = wd.window["covariate_year"]
    w = wd.wdi[(wd.wdi["year"] == year) & wd.wdi["iso3"].isin(wd.nodes)].dropna(subset=["population", "gdp_pc_ppp_const"])
    cw = C.crosswalk().set_index("iso3")
    w = w.assign(lp=np.log(w["population"]), lg=np.log(w["gdp_pc_ppp_const"]))
    z = w[["lp", "lg"]]
    w[["zp", "zg"]] = ((z - z.mean()) / z.std()).to_numpy()
    w = w.set_index("iso3")
    pool = [c for c in w.index if cw.loc[c, "continent"] != "Africa"] if len(w) else []
    rows = []
    for f in focus:
        if f not in w.index:
            rows.append({"focus": f, "comparator": None, "distance": np.nan, "note": "no WDI covariates"})
            continue
        d = np.sqrt((w.loc[pool, "zp"] - w.loc[f, "zp"]) ** 2 + (w.loc[pool, "zg"] - w.loc[f, "zg"]) ** 2)
        for c, dist in d.sort_values().head(per_origin).items():
            rows.append({"focus": f, "comparator": c, "distance": float(dist), "note": ""})
    return pd.DataFrame(rows)


def run_alignment(wd: WindowData, collab_col: str = "full", tag: str = "", *, drop_dest_types: tuple[str, ...] = ()) -> dict:
    cfg = load_config()["alignment"]
    L = layers(wd, collab_col)
    mig, col = L["migration"], L["collaboration"]
    col_full = layers(wd, "full")["collaboration"] if collab_col != "full" else None
    if drop_dest_types:
        bad = [d for d, t in wd.dest_types.items() if any(x in str(t).split() for x in drop_dest_types) and d in mig.index]
        keep = [n for n in mig.nodes if n not in bad]
        mig, col = mig.restrict(keep), col.restrict(keep)
        col_full = col_full.restrict(keep) if col_full is not None else None
    em = mig.W.sum(1)
    # minimum-information rule on distinct international articles in the window,
    # identical for every counting method (not on pair incidences or weights)
    ia = wd.intl_articles.reindex(mig.nodes).fillna(0).to_numpy()
    eligible = [n for i, n in enumerate(mig.nodes) if ia[i] >= cfg["min_origin_intl_papers"] and em[i] >= cfg["min_origin_emigrants"]]
    tab = A.alignment_table(mig, col, eligible, seed=cfg_seed(), ks=tuple(cfg["top_k"]),
                            n_perm=cfg["null_draws"], n_boot=cfg["bootstrap_draws"], col_full=col_full,
                            rarefy_n=cfg.get("rarefy_n"))
    tab["intl_articles"] = wd.intl_articles.reindex(tab["origin"]).to_numpy()
    out = wd.output.set_index("iso3")["articles"]
    tab["log_output"] = np.log(out.reindex(tab["origin"]).to_numpy().astype(float))
    year = wd.window["covariate_year"]
    inc = wd.wdi[wd.wdi["year"] == year].set_index("iso3")["income_id"]
    hic = np.array([inc.get(d) == "HIC" for d in mig.nodes])
    shares = []
    for o in tab["origin"]:
        i = mig.index[o]
        row = mig.W[i]
        shares.append(float(row[hic].sum() / row.sum()) if row.sum() > 0 else np.nan)
    tab["hi_income_share"] = shares
    cw = C.crosswalk().set_index("iso3")
    tab["subregion"] = tab["origin"].map(cw["subregion"])
    tab["ssa"] = tab["origin"].map(cw["ssa"])
    suffix = f"_{tag}" if tag else ""
    tab.to_csv(PATHS.tables / f"alignment_{wd.name}{suffix}.csv", index=False)
    res = {"h1": A.h1_test(tab), "h2": A.h2_test(tab), "n_eligible": len(eligible), "collab_col": collab_col}
    return res


def run_gravity(wd: WindowData, y: str = "full", tag: str = "", models: dict[str, list[str]] | None = None,
                cv: bool = True, dyads: pd.DataFrame | None = None) -> dict:
    cfg = load_config()["gravity"]
    d = (wd.dyads if dyads is None else dyads).dropna(subset=[c for c in BASE if c in (wd.dyads if dyads is None else dyads)])
    models = models or MODELS
    results, tables = {}, []
    for name, cov in models.items():
        cov = [c for c in cov if c in d]
        r = G.fit_ppml(d, y, cov, name=name)
        results[name] = r
        tables.append(r.table())
    tab = pd.concat(tables, ignore_index=True)
    suffix = f"_{tag}" if tag else ""
    tab.to_csv(PATHS.tables / f"gravity_{wd.name}{suffix}.csv", index=False)
    summary = {name: {"nobs": r.nobs, "pseudo_r2": r.pseudo_r2, "deviance": r.deviance, "converged": r.converged,
                      "dropped": r.dropped_countries, "dropped_constant_covariates": r.extra["dropped_constant_covariates"]}
               for name, r in results.items()}
    if "M3_dir" in results:
        summary["wald_mob_up_eq_down"] = G.wald_equal(results["M3_dir"], "ln_mob_up", "ln_mob_down")
    if "M3_dir_both" in results:
        summary["wald_mig_up_eq_down"] = G.wald_equal(results["M3_dir_both"], "ln_mig_up", "ln_mig_down")
    if "M2" in results and "M3" in results:
        g2, g3 = results["M2"].params["ln_mig"], results["M3"].params["ln_mig"]
        summary["attenuation_ln_mig_M2_to_M3"] = float(1 - g3 / g2) if g2 != 0 else np.nan
    summary["vif"] = G.vif(d, [c for c in BASE + ["ln_mig", "ln_mob"] if c in d]).to_dict("records")
    summary["corr_ln_mig_ln_mob"] = float(np.corrcoef(d["ln_mig"], d["ln_mob"])[0, 1])
    if cv:
        cvm = {k: [c for c in v if c in d] for k, v in models.items() if k in ("M1", "M2", "M3", "M1_mob")}
        cvt = G.cross_validate(d, y, cvm, k=cfg["cv_folds"], seed=cfg_seed())
        cvt.to_csv(PATHS.tables / f"gravity_cv_{wd.name}{suffix}.csv", index=False)
        summary["cv"] = [G.cv_compare(cvt, "M1", "M2"), G.cv_compare(cvt, "M2", "M3"),
                         G.cv_compare(cvt, "M1", "M1_mob"), G.cv_compare(cvt, "M1_mob", "M3")]
    with open(PATHS.models / f"gravity_{wd.name}{suffix}.json", "w") as fh:
        json.dump(summary, fh, indent=2, default=float)
    return {"summary": summary, "results": results, "table": tab}


def run_residuals(wd: WindowData, grav: dict, tag: str = "") -> pd.DataFrame:
    cfg = load_config()["residuals"]
    r = grav["results"][cfg["baseline_model"]]
    alpha = R.nb2_alpha(r.extra["y"], r.mu)
    pred = R.predictive(r, alpha, draws=500, seed=cfg_seed())
    fl = R.flag(pred, q=cfg["fdr_q"], min_expected=cfg["min_expected"], min_log_ratio=cfg["min_log_ratio"],
                missing_min_expected=cfg["missing_link_min_expected"])
    d = wd.dyads.set_index(["a", "b"])
    for v in ["mig_ab", "mig_ba", "mob_ab", "mob_ba", "distw", "comlang_off", "colony", "contig"]:
        if v in d:
            fl[v] = d[v].reindex(pd.MultiIndex.from_frame(fl[["a", "b"]])).to_numpy()
    fl["nb_alpha"] = alpha
    suffix = f"_{tag}" if tag else ""
    fl.to_csv(PATHS.tables / f"residuals_{wd.name}{suffix}.csv", index=False)
    return fl


def run_topology(wd: WindowData, tag: str = "") -> dict:
    """E2 (plan v1.2): unit-free, null-calibrated topology comparisons."""
    from ..networks.nulls import expected, layer_alpha
    cfg = load_config()["topology"]
    cw = C.crosswalk().set_index("iso3")
    part = {n: cw.loc[n, "subregion"] for n in wd.nodes}
    tables = []
    alpha_full = None
    for col in ["full", "frac"]:
        L = layers(wd, col)
        named = {"migration": L["migration"], "scholars": L["scholars"], f"collab_{col}": L["collaboration"]}
        for lname, layer in named.items():
            if col == "frac" and lname in ("migration", "scholars"):
                continue
            a = None
            if lname == "collab_full":
                sym = layer.symmetrized()
                alpha_full = layer_alpha(sym.W, expected(sym.W, False), False)
                a = alpha_full
            elif lname == "collab_frac":
                a = alpha_full  # fractional weights: dispersion taken from the full-count layer
            pz = T.participation_z(layer, part, draws=cfg["null_draws"], seed=cfg_seed(), alpha=a)
            bb = T.backbone_betweenness(layer, cfg["backbone_alpha"], null_draws=cfg.get("betweenness_null_draws", 100),
                                        seed=cfg_seed(), alpha=a)
            tables.append(pz.merge(bb.drop(columns=["layer", "null_alpha"], errors="ignore"), on="iso3"))
    topo = pd.concat(tables, ignore_index=True)
    suffix = f"_{tag}" if tag else ""
    topo.to_csv(PATHS.tables / f"topology_{wd.name}{suffix}.csv", index=False)
    L = layers(wd, "full")
    ami, parts = T.community_agreement(L, seed=cfg_seed(), draws=cfg.get("community_null_draws", 100))
    ami.to_csv(PATHS.tables / f"communities_ami_{wd.name}{suffix}.csv", index=False)
    pd.DataFrame([{"iso3": n, **{k: parts[k].get(n) for k in parts}} for n in wd.nodes]).to_csv(
        PATHS.tables / f"communities_{wd.name}{suffix}.csv", index=False)
    T.layer_summary({**L, "migration_sym": L["migration"].symmetrized()}).to_csv(
        PATHS.tables / f"layer_summary_{wd.name}{suffix}.csv", index=False)
    # Collaboration-specific bridge (plan v1.2): for every backbone alpha and both
    # counting methods, (i) positive betweenness in the co-authorship backbone,
    # (ii) co-authorship betweenness above its own null median (calibrated score
    # > 0.5), and (iii) calibrated score higher in co-authorship than in migration.
    alphas = cfg["backbone_alpha"]
    piv = {"migration": topo[topo["layer"] == "migration"].set_index("iso3"),
           "collab_full": topo[topo["layer"] == "collaboration_full"].set_index("iso3"),
           "collab_frac": topo[topo["layer"] == "collaboration_frac"].set_index("iso3")}
    rows = []
    for n in wd.nodes:
        conds = []
        for a in alphas:
            m = piv["migration"][f"betweenness_calib_a{a}"].get(n, np.nan)
            for lname in ["collab_full", "collab_frac"]:
                raw = piv[lname][f"betweenness_a{a}"].get(n, 0.0)
                cal = piv[lname][f"betweenness_calib_a{a}"].get(n, np.nan)
                conds.append(bool(raw > 0 and cal > 0.5 and cal > m))
        rows.append({"iso3": n, "collab_specific_bridge": bool(all(conds)), "share_conditions": float(np.mean(conds))})
    bridges = pd.DataFrame(rows)
    bridges.to_csv(PATHS.tables / f"bridges_{wd.name}{suffix}.csv", index=False)
    return {"ami": ami.to_dict("records"), "n_collab_specific_bridges": int(bridges["collab_specific_bridge"].sum())}


def run_window(name: str, *, robustness: bool = True) -> dict:
    PATHS.ensure()
    cfg = load_config()
    wd = load_window(name)
    wd.universe.to_csv(PATHS.tables / f"universe_{name}.csv", index=False)
    wd.dyads.to_csv(PATHS.processed / f"dyads_{name}.csv", index=False)
    summary: dict = {"window": name, "label": wd.window["label"], "n_countries": len(wd.nodes),
                     "n_dyads": len(wd.dyads)}
    comp = comparison_origins(wd, cfg["countries"]["focus_origins"], cfg["countries"]["comparators_per_origin"])
    comp.to_csv(PATHS.tables / f"comparators_{name}.csv", index=False)
    summary["alignment"] = run_alignment(wd, "full")
    grav = run_gravity(wd, "full")
    summary["gravity"] = grav["summary"]
    fl = run_residuals(wd, grav)
    summary["residual_categories"] = fl["category"].value_counts().to_dict()
    summary["topology"] = run_topology(wd)
    if robustness:
        rob = {}
        if "frac" in wd.dyads:
            rob["R1_alignment_frac"] = run_alignment(wd, "frac", "frac")
            rob["R1_gravity_frac"] = run_gravity(wd, "frac", "frac", cv=False)["summary"]
        if "full_nomega" in wd.dyads:
            rob["R2_gravity_nomega"] = run_gravity(wd, "full_nomega", "nomega", cv=False)["summary"]
        rob["R3_gravity_dist_ethno"] = run_gravity(
            wd.__class__(**{**wd.__dict__, "dyads": wd.dyads.assign(ln_distw=wd.dyads["ln_dist"], comlang_off=wd.dyads["comlang_ethno"])}),
            "full", "dist_ethno", cv=False)["summary"]
        rob["R4_alignment_birthplace_only"] = run_alignment(wd, "full", "birthplace", drop_dest_types=("C", "I"))
        if "ln_mob_scopus" in wd.dyads:
            m = {"M3_scopus": BASE + ["ln_mig", "ln_mob_scopus"], "M1_mob_scopus": BASE + ["ln_mob_scopus"]}
            rob["R6_gravity_scopus"] = run_gravity(wd, "full", "scopus", models=m, cv=False)["summary"]
        rob["R9_gravity_zero_dummy"] = run_gravity(wd, "full", "zerodummy",
                                                   models={"M2_nz": BASE + ["ln_mig_nz", "mig_zero"],
                                                           "M3_nz": BASE + ["ln_mig_nz", "mig_zero", "ln_mob"]}, cv=False)["summary"]
        big = wd.universe[(wd.universe["included"]) & (wd.universe["population"].fillna(np.inf) >= 5e6)]["iso3"]
        sub = wd.dyads[wd.dyads["a"].isin(big) & wd.dyads["b"].isin(big)]
        rob["R7_gravity_pop5m"] = run_gravity(wd, "full", "pop5m", cv=False, dyads=sub)["summary"]
        r = grav["results"]["M2"]
        alpha = R.nb2_alpha(r.extra["y"], r.mu)
        gd = wd.dyads.dropna(subset=BASE)
        nb = pd.concat([G.fit_negbin(gd, "full", MODELS[m], alpha, m) for m in ("M2", "M3")])
        nb.to_csv(PATHS.tables / f"gravity_negbin_{name}.csv", index=False)
        jk = pd.concat([G.jackknife(gd, "full", MODELS["M3"], ["ln_mig", "ln_mob"], "M3")])
        jk.to_csv(PATHS.tables / f"jackknife_{name}.csv", index=False)
        rob["R5_jackknife"] = {t: {"min": float(jk[t].min()), "max": float(jk[t].max()),
                                   "most_influential": jk.loc[jk[f"delta_{t}"].abs().idxmax(), "dropped"]}
                               for t in ["ln_mig", "ln_mob"]}
        summary["robustness"] = rob
    with open(PATHS.models / f"summary_{name}.json", "w") as fh:
        json.dump(summary, fh, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return summary
