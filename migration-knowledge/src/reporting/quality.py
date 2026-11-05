"""Data-quality report (research/data_quality_report.md), generated from the
processed data and outputs. Sections that need data that has not been
acquired say so explicitly instead of being silently omitted."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..cleaning.openalex import count_pairs
from ..config import PATHS, load_config
from ..provenance import utcnow


def _csv(p: Path) -> pd.DataFrame | None:
    return pd.read_csv(p, keep_default_na=False, na_values=[""]) if p.exists() else None


def _md(df: pd.DataFrame, n: int = 30) -> str:
    if df is None or df.empty:
        return "_none_\n"
    return df.head(n).to_markdown(index=False) + ("\n\n_… truncated_\n" if len(df) > n else "\n")


def section_access() -> str:
    p = PATHS.outputs / "access_check.json"
    if not p.exists():
        return "## 0. Data access\n\nNo access check recorded.\n"
    res = json.loads(p.read_text())
    rows = pd.DataFrame([{"source": k, "status": v} for k, v in res.items()])
    return "## 0. Data access (latest check)\n\n" + _md(rows)


def section_manifest() -> str:
    if not PATHS.manifest.exists():
        return "## 1. Provenance\n\nNo files have been acquired (MANIFEST.jsonl is empty).\n"
    rows = [json.loads(l) for l in PATHS.manifest.read_text().splitlines() if l.strip()]
    df = pd.DataFrame(rows)[["source", "file", "retrieved_utc", "rows", "bytes", "license", "sha256"]]
    df["sha256"] = df["sha256"].str[:12]
    return "## 1. Provenance (data/raw/MANIFEST.jsonl)\n\n" + _md(df, 60)


def section_migration() -> str:
    m = _csv(PATHS.processed / "migration_stocks.csv")
    if m is None:
        return "## 2. UN DESA migrant stocks\n\n_Not available: data not acquired._\n"
    out = ["## 2. UN DESA migrant stocks\n"]
    s = m.groupby("year").agg(corridors=("stock", "size"), reported=("corridor_status", lambda x: (x == "reported").sum()),
                              reported_zero=("corridor_status", lambda x: (x == "reported_zero").sum()),
                              missing=("corridor_status", lambda x: (x == "missing").sum()),
                              total_stock=("stock", "sum")).reset_index()
    out.append("Country-to-country corridors by year (after harmonization):\n\n" + _md(s))
    cov = _csv(PATHS.processed / "undesa_destination_coverage.csv")
    if cov is not None:
        c = cov.groupby("year")["attributed_share"].describe()[["count", "mean", "min", "25%", "50%"]].reset_index()
        out.append("Share of each destination's migrant stock attributable to identifiable origin countries "
                   "(remainder: 'Other'/unknown origins):\n\n" + _md(c))
        low = cov[cov["attributed_share"] < 0.8].sort_values("attributed_share")[["dest_iso3", "year", "attributed_share", "dest_data_type"]]
        out.append("Destinations with < 80% of stock attributed to countries:\n\n" + _md(low, 25))
        t = cov[cov["year"] == 2015]["dest_data_type"].fillna("").value_counts().reset_index()
        out.append("Destination data types, 2015 (B = birthplace, C = citizenship, R = refugees added, I = imputed):\n\n" + _md(t))
    exc = _csv(PATHS.tables / "undesa_excluded_rows.csv")
    if exc is not None:
        out.append(f"Rows excluded as aggregates, residual origins or unmatched codes: {int(exc['rows'].sum()):,} "
                   f"(see outputs/tables/undesa_excluded_rows.csv).\n")
    return "\n".join(out)


def section_scholarly() -> str:
    s = _csv(PATHS.processed / "scholarly_moves.csv")
    if s is None:
        return "## 3. Scholarly mobility\n\n_Not available: data not acquired._\n"
    t = s.groupby(["source", "year"])["moves"].agg(["size", "sum"]).reset_index().rename(columns={"size": "pairs", "sum": "moves"})
    out = ["## 3. Scholarly mobility\n", _md(t, 60)]
    if set(s["source"]) >= {"openalex", "scopus"}:
        w = s.pivot_table(index=["origin_iso3", "dest_iso3"], columns="source", values="moves", aggfunc="sum").fillna(0)
        r = np.corrcoef(np.log1p(w["openalex"]), np.log1p(w["scopus"]))[0, 1]
        out.append(f"Correlation of log(1+moves) between OpenAlex and Scopus releases (pairs, all years): {r:.3f}\n")
    return "\n".join(out)


def section_openalex() -> str:
    out = ["## 4. OpenAlex co-authorship\n"]
    files = sorted(PATHS.processed.glob("collab_*_*.csv"))
    if not files:
        return out[0] + "\n_Not available: data not acquired._\n"
    rows = []
    for f in files:
        c = _csv(f)
        both = c["symmetric_ok"].notna()
        rows.append({"window": f.stem.replace("collab_", ""), "pairs_with_collab": int((c["full"] > 0).sum()),
                     "total_full": float(c["full"].sum()), "total_frac": float(c["frac"].sum()),
                     "pairs_both_sides_queried": int(both.sum()),
                     "symmetry_failures": int((c.loc[both, "symmetric_ok"].astype(str).isin(["False", "0", "0.0"])).sum()),
                     "share_full_in_mega_works": float(1 - c["full_nomega"].sum() / c["full"].sum()) if c["full"].sum() else np.nan})
    out.append("Pair counts by window. Symmetry check: the count for (X, Y) from X's query must equal the count from Y's query.\n\n" + _md(pd.DataFrame(rows)))
    cov = _csv(PATHS.raw / "openalex" / "coverage_by_year.csv")
    if cov is not None:
        tot = cov[cov["k"] == -1].set_index("year")["works"]
        k0 = cov[cov["k"] == 0].set_index("year")["works"].reindex(tot.index).fillna(0)
        intl = cov[cov["k"] >= 2].groupby("year")["works"].sum().reindex(tot.index).fillna(0)
        t = pd.DataFrame({"articles": tot, "no_country_info_share": k0 / tot, "international_share": intl / tot}).reset_index()
        out.append("Coverage of country information among filtered journal articles:\n\n" + _md(t))
    # validation of group_by counts against work-level downloads
    vrows = []
    for wf in sorted((PATHS.raw / "openalex" / "works").glob("*.jsonl")) if (PATHS.raw / "openalex" / "works").exists() else []:
        works = [json.loads(l) for l in wf.read_text().splitlines() if l.strip()]
        iso2, y0, y1 = wf.stem.split("_")
        direct = count_pairs(works)
        inter = count_pairs(works, mode="inter_author")
        foc = direct[(direct["a"] == iso2) | (direct["b"] == iso2)]
        foc_i = inter[(inter["a"] == iso2) | (inter["b"] == iso2)]
        kp = _csv(PATHS.raw / "openalex" / f"kpairs_{y0}_{y1}" / f"{iso2}.csv")
        agg_total = float(kp[kp["partner"] != iso2]["n_works"].sum()) if kp is not None else np.nan
        vrows.append({"origin": iso2, "window": f"{y0}-{y1}", "works_downloaded": len(works),
                      "pair_count_worklevel": float(foc["full"].sum()), "pair_count_groupby": agg_total,
                      "inter_author_share": float(foc_i["full"].sum() / foc["full"].sum()) if foc["full"].sum() else np.nan})
    if vrows:
        out.append("Validation: partner counts from work-level records vs aggregate group_by queries, and the share of "
                   "pairs that survive inter-author counting (R8):\n\n" + _md(pd.DataFrame(vrows)))
    return "\n".join(out)


def section_universe() -> str:
    out = ["## 5. Country universe and exclusions\n"]
    for w in ("primary", "earlier", "later"):
        u = _csv(PATHS.tables / f"universe_{w}.csv")
        if u is None:
            continue
        out.append(f"**{w}**: {int(u['included'].astype(str).isin(['True','1']).sum())} included of {len(u)} candidates.\n")
        exc = u[~u["included"].astype(str).isin(["True", "1"])]["reasons"].str.split(";").explode().value_counts().reset_index()
        out.append(_md(exc))
    if len(out) == 1:
        out.append("_Not available: analysis not run._\n")
    for name in ("harmonization_special_cases", "harmonization_openalex_2015_2019", "harmonization_cepii", "harmonization_wdi"):
        h = _csv(PATHS.tables / f"{name}.csv")
        if h is not None:
            out.append(f"\n`{name}.csv`:\n\n" + _md(h, 40))
    return "\n".join(out)


def section_biases() -> str:
    return """## 6. Known biases and limitations of the inputs

* **OpenAlex affiliation coverage** varies by country, language and field. Works without any country information
  cannot enter the network, and a work where only some authors have affiliations understates its international ties.
* **Institutional, not personal, geography.** Co-authorship pairs come from institutional affiliations. A single author
  with affiliations in two countries creates a pair; R8 quantifies this for the focus origins.
* **Mega-collaborations** (more than 20 countries; consortia such as Global Burden of Disease or particle-physics
  experiments) can dominate small countries' full counts; R2 removes them exactly.
* **UN DESA stocks** are estimates, mix birthplace- and citizenship-based destination data, add refugees in some
  destinations, and lump many origins into 'Other' for some destinations (Section 2).
* **Scholarly mobility** is inferred from changes in modal affiliation country between publications. It misses
  non-publishing movers, is sensitive to affiliation errors, and is built from the same bibliographic source
  (OpenAlex) as the outcome in the primary analysis.
"""


def write_report() -> Path:
    cfg = load_config()
    parts = [f"# Data quality report\n\nGenerated {utcnow()} by `make quality` from the processed data and outputs. "
             "Every number below is computed. Nothing is hand-entered.\n",
             section_access(), section_manifest(), section_migration(), section_scholarly(), section_openalex(),
             section_universe(), section_biases()]
    path = PATHS.research / "data_quality_report.md"
    path.write_text("\n\n".join(parts), encoding="utf-8")
    return path
