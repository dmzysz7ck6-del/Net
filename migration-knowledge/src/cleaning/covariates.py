"""Clean WDI and CEPII GeoDist into ISO3-keyed covariate tables."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .countries import HarmonizationReport, expand_split, to_iso3

GEO_VARS = ["contig", "comlang_off", "comlang_ethno", "colony", "comcol", "curcol", "col45", "smctry",
            "dist", "distcap", "distw", "distwces"]


def wdi_panel(wdi_long: pd.DataFrame, wdi_countries: pd.DataFrame) -> tuple[pd.DataFrame, HarmonizationReport]:
    """Wide country-year panel; aggregates (WDI region 'Aggregates') removed."""
    aggregates = set(wdi_countries.loc[wdi_countries["region"].str.strip() == "Aggregates", "wdi_code"])
    d = wdi_long[~wdi_long["wdi_code"].isin(aggregates)].copy()
    rep = HarmonizationReport("wdi")
    d["iso3"] = to_iso3(d["wdi_code"], "wdi", rep)
    d = d.dropna(subset=["iso3"])
    wide = d.pivot_table(index=["iso3", "year"], columns="indicator", values="value", aggfunc="first").reset_index()
    wide.columns.name = None
    meta = wdi_countries.assign(iso3=to_iso3(wdi_countries["wdi_code"], "wdi")).dropna(subset=["iso3"])
    wide = wide.merge(meta[["iso3", "region", "income", "income_id"]], on="iso3", how="left")
    return wide, rep


def read_geodist(path: Path) -> pd.DataFrame:
    if path.suffix == ".dta":
        df = pd.read_stata(path)
    elif path.suffix in (".xls", ".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = {"iso_o", "iso_d"} - set(df.columns)
    if missing:
        raise ValueError(f"GeoDist file lacks {missing}")
    return df


def geodist_dyads(df: pd.DataFrame) -> tuple[pd.DataFrame, HarmonizationReport]:
    """Directed GeoDist rows -> ISO3, with legacy codes mapped and split codes
    (YUG, ANT) copied to successors with ``geo_imputed = True``."""
    rep = HarmonizationReport("cepii")
    d = df.copy()
    d["iso_o"] = d["iso_o"].astype(str).str.upper()
    d["iso_d"] = d["iso_d"].astype(str).str.upper()
    # expand split codes on each side (rows are directed, so do o then d)
    eo = expand_split(d, "iso_o")
    d = pd.concat([d, eo], ignore_index=True)
    ed = expand_split(d, "iso_d")
    d = pd.concat([d, ed], ignore_index=True)
    d["geo_imputed"] = d.get("iso_o_imputed", False).fillna(False).astype(bool) | d.get("iso_d_imputed", False).fillna(False).astype(bool)
    d["o"] = to_iso3(d["iso_o"], "cepii", rep)
    d["d"] = to_iso3(d["iso_d"], "cepii", rep)
    d = d.dropna(subset=["o", "d"])
    d = d[d["o"] != d["d"]]
    # A split code's diagonal row (e.g. YUG-YUG) would otherwise become SRB-MNE with
    # 'internal' distance and contig = 0. Such successor-successor pairs are dropped
    # and reported; they are missing from GeoDist, not imputed.
    from .countries import SPECIAL_CASES
    succ_groups = [set(v["iso3"]) for (sch, _), v in SPECIAL_CASES.items() if sch == "cepii" and v["action"] == "split"]
    bad = d.apply(lambda r: any(r["o"] in g and r["d"] in g for g in succ_groups) and bool(r["geo_imputed"]), axis=1) if len(d) else pd.Series(dtype=bool)
    if len(d) and bad.any():
        rep.excluded.update({f"{r.o}-{r.d}": "successor pair created from a split code's diagonal row" for r in d[bad].itertuples()})
        d = d[~bad]
    # prefer original over imputed rows if both exist for a pair
    d = d.sort_values("geo_imputed").drop_duplicates(["o", "d"], keep="first")
    keep = ["o", "d", "geo_imputed"] + [v for v in GEO_VARS if v in d.columns]
    return d[keep].reset_index(drop=True), rep


def undirected_geo(geo: pd.DataFrame) -> pd.DataFrame:
    """Unordered pairs (a < b). Symmetric variables are taken from the a->b row;
    `colony` is symmetrized with max() (a colonial link in either direction)."""
    g = geo.copy()
    g["a"] = np.where(g["o"] < g["d"], g["o"], g["d"])
    g["b"] = np.where(g["o"] < g["d"], g["d"], g["o"])
    agg = {v: "max" for v in ["contig", "comlang_off", "comlang_ethno", "colony", "comcol", "curcol", "col45", "smctry"] if v in g}
    agg.update({v: "mean" for v in ["dist", "distcap", "distw", "distwces"] if v in g})
    agg["geo_imputed"] = "max"
    return g.groupby(["a", "b"], as_index=False).agg(agg)


def read_geodist_geo(path: Path) -> pd.DataFrame:
    """Capital coordinates from geo_cepii (one row per country: cap == 1,
    else the first listed city)."""
    if path.suffix == ".dta":
        g = pd.read_stata(path)
    elif path.suffix in (".xls", ".xlsx"):
        g = pd.read_excel(path)
    else:
        g = pd.read_csv(path)
    g.columns = [c.strip().lower() for c in g.columns]
    code = "iso3" if "iso3" in g.columns else "iso_o"
    g["iso3c"] = to_iso3(g[code].astype(str).str.upper(), "cepii")
    if "cap" in g.columns:
        g = g.sort_values("cap", ascending=False)
    g = g.dropna(subset=["iso3c"]).drop_duplicates("iso3c")
    return g.rename(columns={"iso3c": "iso3"})[["iso3", "lat", "lon"]]
