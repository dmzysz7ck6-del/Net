"""Assemble time-aligned analysis datasets for one design window.

Inputs are the cleaned long tables (all ISO3-keyed):

* migration: origin_iso3, dest_iso3, year, stock, dest_data_type, corridor_status
* mobility:  origin_iso3, dest_iso3, year, moves, source
* collab:    a, b, full, frac (+ optional variants), for the window's years
* output:    iso3, articles (capacity window), intl_articles
* wdi:       iso3, year, population, gdp_current_usd, gdp_pc_ppp_const, income_id
* geo:       a, b, distw, dist, contig, comlang_off, comlang_ethno, colony, comcol, geo_imputed

Outputs
-------
``universe``: node table with inclusion decisions and reasons.
``dyads``: one row per unordered pair {a < b} of universe countries with the
co-authorship outcome, migrant stocks in both directions, scholarly moves in
both directions, geography and the capacity ordering used for H4b.

Temporal alignment is enforced here: only the configured stock year,
mobility years and collaboration years are used (``check_alignment``).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def check_alignment(window: dict, migration: pd.DataFrame, mobility: pd.DataFrame, collab_years: tuple[int, int]) -> None:
    my = window["migrant_stock_year"]
    if set(migration["year"].unique()) != {my}:
        raise ValueError(f"migration table must contain only year {my}, got {sorted(migration['year'].unique())}")
    lo, hi = window["mobility_years"]
    if len(mobility) and (mobility["year"].min() < lo or mobility["year"].max() > hi):
        raise ValueError(f"mobility years outside {lo}-{hi}")
    if tuple(collab_years) != tuple(window["collab_years"]):
        raise ValueError(f"collaboration window {collab_years} != configured {window['collab_years']}")


def select_universe(candidates: list[str], wdi: pd.DataFrame, collab: pd.DataFrame, window: dict,
                    min_population: float, in_all_sources: dict[str, set[str]],
                    wdi_absent_allowlist: tuple[str, ...] = ()) -> pd.DataFrame:
    year = window["covariate_year"]
    pop = wdi[wdi["year"] == year].set_index("iso3")["population"] if len(wdi) else pd.Series(dtype=float)
    intl = pd.concat([collab[["a", "full"]].rename(columns={"a": "iso3"}),
                      collab[["b", "full"]].rename(columns={"b": "iso3"})]).groupby("iso3")["full"].sum()
    rows = []
    for c in sorted(set(candidates)):
        reasons = []
        for src, members in in_all_sources.items():
            if c not in members:
                reasons.append(f"absent_from_{src}")
        p = pop.get(c, np.nan)
        if np.isnan(p):
            if c not in wdi_absent_allowlist:
                reasons.append("no_population_data")
        elif p < min_population:
            reasons.append("population_below_threshold")
        if intl.get(c, 0) <= 0:
            reasons.append("no_international_coauthorship")
        rows.append({"iso3": c, "population": p, "intl_coauthored": float(intl.get(c, 0)),
                     "wdi_missing": bool(np.isnan(p)), "included": not reasons, "reasons": ";".join(reasons)})
    return pd.DataFrame(rows)


def build_dyads(universe: list[str], migration: pd.DataFrame, mobility: pd.DataFrame, collab: pd.DataFrame,
                geo: pd.DataFrame, output: pd.DataFrame, collab_cols=("full", "frac")) -> pd.DataFrame:
    U = sorted(universe)
    pairs = pd.DataFrame([(a, b) for i, a in enumerate(U) for b in U[i + 1:]], columns=["a", "b"])

    def directed_lookup(df: pd.DataFrame, value: str) -> pd.Series:
        return df.groupby(["origin_iso3", "dest_iso3"])[value].sum()

    mig = directed_lookup(migration.fillna({"stock": 0}), "stock")
    mob = directed_lookup(mobility, "moves") if len(mobility) else pd.Series(dtype=float)
    idx_ab = pd.MultiIndex.from_frame(pairs[["a", "b"]])
    idx_ba = pd.MultiIndex.from_frame(pairs[["b", "a"]])
    pairs["mig_ab"] = mig.reindex(idx_ab).fillna(0).to_numpy()
    pairs["mig_ba"] = mig.reindex(idx_ba).fillna(0).to_numpy()
    pairs["mig_reported_ab"] = mig.reindex(idx_ab).notna().to_numpy()
    pairs["mig_reported_ba"] = mig.reindex(idx_ba).notna().to_numpy()
    pairs["mob_ab"] = mob.reindex(idx_ab).fillna(0).to_numpy() if len(mob) else 0.0
    pairs["mob_ba"] = mob.reindex(idx_ba).fillna(0).to_numpy() if len(mob) else 0.0

    c = collab.set_index(["a", "b"])
    for col in collab_cols:
        pairs[col] = c[col].reindex(idx_ab).fillna(0).to_numpy() if col in c else np.nan

    g = geo.set_index(["a", "b"])
    for v in g.columns:
        pairs[v] = g[v].reindex(idx_ab).to_numpy()

    out = output.set_index("iso3")["articles"]
    pairs["out_a"] = out.reindex(pairs["a"]).to_numpy()
    pairs["out_b"] = out.reindex(pairs["b"]).to_numpy()

    # transformations used in the models
    pairs["ln_mig"] = np.log1p(pairs["mig_ab"] + pairs["mig_ba"])
    pairs["mig_zero"] = ((pairs["mig_ab"] + pairs["mig_ba"]) == 0).astype(float)
    pairs["ln_mig_nz"] = np.where(pairs["mig_zero"] == 1, 0.0, np.log(np.maximum(pairs["mig_ab"] + pairs["mig_ba"], 1)))
    pairs["ln_mob"] = np.log1p(pairs["mob_ab"] + pairs["mob_ba"])
    if "distw" in pairs:
        pairs["ln_distw"] = np.log(pairs["distw"])
    if "dist" in pairs:
        pairs["ln_dist"] = np.log(pairs["dist"])
    # capacity ordering for direction tests (H4b): 'low' = lower capacity-window output
    a_low = pairs["out_a"] <= pairs["out_b"]
    pairs["low"] = np.where(a_low, pairs["a"], pairs["b"])
    pairs["high"] = np.where(a_low, pairs["b"], pairs["a"])
    pairs["mob_up"] = np.where(a_low, pairs["mob_ab"], pairs["mob_ba"])      # low -> high
    pairs["mob_down"] = np.where(a_low, pairs["mob_ba"], pairs["mob_ab"])    # high -> low
    pairs["mig_up"] = np.where(a_low, pairs["mig_ab"], pairs["mig_ba"])
    pairs["mig_down"] = np.where(a_low, pairs["mig_ba"], pairs["mig_ab"])
    for v in ["mob_up", "mob_down", "mig_up", "mig_down"]:
        pairs[f"ln_{v}"] = np.log1p(pairs[v])
    return pairs


def missing_geography(d: pd.DataFrame) -> pd.DataFrame:
    """Pairs lacking any gravity covariate (e.g. successor pairs of split
    GeoDist codes). They are excluded from gravity models and reported."""
    cols = [v for v in ["ln_distw", "contig", "comlang_off", "colony", "comcol"] if v in d]
    return d.loc[d[cols].isna().any(axis=1), ["a", "b"]]


def validate_dyads(d: pd.DataFrame) -> list[str]:
    """Regression-input integrity checks; returns a list of problems.
    Missing geography is reported separately (``missing_geography``)."""
    problems = []
    if not (d["a"] < d["b"]).all():
        problems.append("pairs not canonical (a < b)")
    if d.duplicated(["a", "b"]).any():
        problems.append("duplicate pairs")
    n = len(set(d["a"]) | set(d["b"]))
    if len(d) != n * (n - 1) // 2:
        problems.append(f"expected {n*(n-1)//2} pairs for {n} countries, got {len(d)}")
    for v in ["full", "mig_ab", "mig_ba", "mob_ab", "mob_ba"]:
        if v in d and (d[v] < 0).any():
            problems.append(f"negative values in {v}")
    if "frac" in d and "full" in d and (d["frac"] > d["full"] + 1e-9).any():
        problems.append("fractional count exceeds full count")
    return problems
