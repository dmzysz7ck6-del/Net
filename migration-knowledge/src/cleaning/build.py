"""Build the processed data contract from raw downloads.

Raw files are never modified; every harmonization decision is written to
``outputs/tables/harmonization_*.csv`` so excluded and unmatched codes are
visible in the data-quality report.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import PATHS, load_config
from . import countries as C
from . import covariates as COV
from . import openalex as OA
from . import scholarly as SCH
from . import undesa as UN


def _save_report(rep, name: str) -> None:
    rep.as_frame().to_csv(PATHS.tables / f"harmonization_{name}.csv", index=False)


def build_migration() -> pd.DataFrame:
    path = next(iter(sorted((PATHS.raw / "undesa").glob("*destination_and_origin*.xlsx"))), None)
    if path is None:
        raise FileNotFoundError("UN DESA workbook not found; run `make acquire`")
    table = UN.read_table(path)
    years = sorted({w["migrant_stock_year"] for w in load_config()["windows"].values()})
    long, excluded, rep = UN.tidy(table, years=years)
    long.to_csv(PATHS.processed / "migration_stocks.csv", index=False)
    excluded.to_csv(PATHS.tables / "undesa_excluded_rows.csv", index=False)
    _save_report(rep["dest"], "undesa_destination")
    _save_report(rep["origin"], "undesa_origin")
    cov = pd.concat([UN.destination_coverage(table, y) for y in years], ignore_index=True)
    cov.to_csv(PATHS.processed / "undesa_destination_coverage.csv", index=False)
    return long


def build_scholarly() -> pd.DataFrame:
    import hashlib
    frames, reports, used = [], [], []
    for source in ("openalex", "scopus"):
        files = SCH.find_flow_files(PATHS.raw / "scholarly", source)
        seen_hash, seen_keys = set(), None
        src_frames = []
        for f in files:
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            if h in seen_hash:  # identical copy (e.g. extracted from a zip next to the CSV)
                continue
            seen_hash.add(h)
            df, rep = SCH.parse_flows(f, source)
            keys = set(map(tuple, df[["origin_iso3", "dest_iso3", "year"]].to_numpy()))
            if seen_keys is not None and keys & seen_keys:
                raise ValueError(f"{f.name} repeats corridor-years already read for source {source}; "
                                 "choose exactly one bilateral flow file per source")
            seen_keys = keys if seen_keys is None else seen_keys | keys
            src_frames.append(df)
            reports.append(rep.as_frame().assign(file=f.name))
            used.append({"source": source, "file": str(f.relative_to(PATHS.root)), "sha256": h, "rows": len(df),
                         "columns": json.dumps(df.attrs.get("columns", {}))})
        frames += src_frames
    pd.DataFrame(used).to_csv(PATHS.tables / "scholarly_files_used.csv", index=False)
    if not frames:
        raise FileNotFoundError("no bilateral scholarly flow files found; run `make acquire`")
    out = pd.concat(frames, ignore_index=True)
    out = out.groupby(["origin_iso3", "dest_iso3", "year", "source"], as_index=False)["moves"].sum()
    out.to_csv(PATHS.processed / "scholarly_moves.csv", index=False)
    pd.concat(reports).to_csv(PATHS.tables / "harmonization_scholarly.csv", index=False)
    return out


def build_collab() -> None:
    cfg = load_config()
    mega = cfg["openalex"]["mega_country_threshold"]
    for f in sorted((PATHS.raw / "openalex").glob("kpairs_*_*.csv")):
        y0, y1 = f.stem.split("_")[1:3]
        kt = pd.read_csv(f, keep_default_na=False, na_values=[""])
        rep = C.HarmonizationReport(f"openalex_{y0}_{y1}")
        kt["focal"] = C.to_iso3(kt["focal"], "iso2", rep)
        kt["partner"] = C.to_iso3(kt["partner"], "iso2", rep)
        kt = kt.dropna(subset=["focal", "partner"])
        if "sum_check" in kt:
            sc = kt.drop_duplicates(["focal", "k"])[["focal", "k", "k_total_works", "sum_check"]]
            sc.to_csv(PATHS.tables / f"openalex_sum_check_{y0}_{y1}.csv", index=False)
            # works-weighted mean deviation of sum(n_k(X,Y)) / (k N_k(X)) from 1
            dev = float(np.average(np.abs(sc["sum_check"] - 1), weights=sc["k_total_works"])) if len(sc) else 0.0
            (PATHS.tables / f"openalex_sum_check_{y0}_{y1}.json").write_text(json.dumps(
                {"weighted_mean_abs_deviation": dev, "fractional_counts_valid": dev <= 0.01}))
        allk = OA.aggregate_k_table(kt)
        nomega = OA.aggregate_k_table(kt, max_countries=mega)[["a", "b", "full", "frac"]].rename(
            columns={"full": "full_nomega", "frac": "frac_nomega"})
        out = allk.merge(nomega, on=["a", "b"], how="left").fillna({"full_nomega": 0, "frac_nomega": 0})
        out.to_csv(PATHS.processed / f"collab_{y0}_{y1}.csv", index=False)
        # distinct international articles per focal country in the window
        # (sum over k >= 2 of the number of its works with exactly k countries)
        if "k_total_works" in kt:
            nodes = (kt[kt["k"] >= 2].drop_duplicates(["focal", "k"]).groupby("focal")["k_total_works"].sum()
                     .rename("intl_articles").reset_index().rename(columns={"focal": "iso3"}))
            nodes.to_csv(PATHS.processed / f"collab_{y0}_{y1}_nodes.csv", index=False)
        _save_report(rep, f"openalex_{y0}_{y1}")
    for f in sorted((PATHS.raw / "openalex").glob("output_*_*.csv")):
        y0, y1 = f.stem.split("_")[1:3]
        o = pd.read_csv(f, keep_default_na=False, na_values=[""])
        rep = C.HarmonizationReport(f"openalex_output_{y0}_{y1}")
        o["iso3"] = C.to_iso3(o["iso2"], "iso2", rep)
        o.dropna(subset=["iso3"])[["iso3", "articles", "intl_articles", "kdist"]].to_csv(
            PATHS.processed / f"output_{y0}_{y1}.csv", index=False)


def build_covariates() -> None:
    wl = pd.read_csv(PATHS.raw / "wdi" / "wdi_long.csv", keep_default_na=False, na_values=[""])
    wc = pd.read_csv(PATHS.raw / "wdi" / "wdi_countries.csv", keep_default_na=False, na_values=[""])
    panel, rep = COV.wdi_panel(wl, wc)
    panel.to_csv(PATHS.processed / "wdi_panel.csv", index=False)
    _save_report(rep, "wdi")
    dist = next((p for p in (PATHS.raw / "cepii").glob("dist_cepii.*") if p.suffix in (".dta", ".xls", ".xlsx", ".csv")), None)
    if dist is None:
        raise FileNotFoundError("CEPII dist_cepii not found; run `make acquire`")
    geo, rep = COV.geodist_dyads(COV.read_geodist(dist))
    _save_report(rep, "cepii")
    COV.undirected_geo(geo).to_csv(PATHS.processed / "geo_dyads.csv", index=False)
    gpath = next((p for p in (PATHS.raw / "cepii").glob("geo_cepii.*") if p.suffix in (".dta", ".xls", ".xlsx", ".csv")), None)
    if gpath is not None:
        g = COV.read_geodist_geo(gpath)
        g.to_csv(PATHS.processed / "country_coords.csv", index=False)


def build_all() -> None:
    PATHS.ensure()
    build_migration()
    build_scholarly()
    build_collab()
    build_covariates()
    C.special_cases_frame().to_csv(PATHS.tables / "harmonization_special_cases.csv", index=False)
