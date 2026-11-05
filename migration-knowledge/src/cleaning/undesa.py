"""Parse the UN DESA IMS 2024 destination-and-origin workbook.

Orientation (tested): each data row is one (destination, origin) corridor;
the value is the number of international migrants **living in the
destination** who were **born in** (or, where the destination reports
citizenship, are citizens of) the origin. We emit ``origin_iso3 -> dest_iso3``.

The parser locates the header row by content rather than position, so
cosmetic layout changes in the workbook do not silently shift columns.

Missing vs zero: cells containing ``..``, ``-`` or blanks are missing
(``NaN``); numeric 0 is a reported zero. Corridors that do not appear at all
are "unreported" — downstream code treats them as zero for network
construction but keeps the distinction in ``corridor_status``.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .countries import HarmonizationReport, to_iso3

HEADER_KEY = "location code of destination"
SEX_LABELS = {"both sexes": "both", "male": "male", "female": "female", "males": "male", "females": "female"}
MISSING_TOKENS = {"..", "...", "-", "–", "", "nan", "None"}


def _norm(x) -> str:
    return re.sub(r"\s+", " ", str(x)).strip().lower()


def find_header(raw: pd.DataFrame) -> int:
    for i in range(min(60, len(raw))):
        if any(_norm(v) == HEADER_KEY for v in raw.iloc[i].tolist()):
            return i
    raise ValueError(f"could not find a header row containing {HEADER_KEY!r}")


def build_columns(raw: pd.DataFrame, h: int) -> list[str]:
    header = [_norm(v) for v in raw.iloc[h].tolist()]
    # sex labels sit in a super-header row above the year columns (merged cells)
    def sex_of(v: str) -> str | None:
        if re.search(r"\bfemales?\b", v):
            return "female"
        if re.search(r"\bmales?\b", v):
            return "male"
        if re.search(r"both sexes|\btotal\b", v):
            return "both"
        return None

    sex_row = None
    for r in range(max(0, h - 3), h):
        vals = [_norm(v) for v in raw.iloc[r].tolist()]
        if any(sex_of(v) for v in vals):
            sex_row = vals
    current = None
    names = []
    for j, v in enumerate(header):
        if sex_row is not None and sex_of(sex_row[j]):
            current = sex_of(sex_row[j])
        m = re.fullmatch(r"(\d{4})(\.0)?", v)
        if m:
            names.append(f"{current or 'both'}_{m.group(1)}")
        else:
            names.append(v)
    years = [n for n in names if re.fullmatch(r"(both|male|female)_\d{4}", n)]
    if len(years) != len(set(years)):
        raise ValueError("year columns are not unique after naming; sex super-header not recognized")
    return names


def read_table(path: Path, sheet: str | None = None) -> pd.DataFrame:
    xl = pd.ExcelFile(path)
    if sheet is None:
        sheet = next((s for s in xl.sheet_names if _norm(s) in {"table 1", "table1"}), xl.sheet_names[0])
    raw = xl.parse(sheet, header=None, dtype=object)
    h = find_header(raw)
    cols = build_columns(raw, h)
    df = raw.iloc[h + 1:].copy()
    df.columns = cols
    df = df.dropna(how="all")
    rename = {}
    for c in df.columns:
        if c.startswith("region, development group, country or area of destination"):
            rename[c] = "dest_name"
        elif c.startswith("region, development group, country or area of origin"):
            rename[c] = "origin_name"
        elif c == "location code of destination":
            rename[c] = "dest_code"
        elif c == "location code of origin":
            rename[c] = "origin_code"
        elif c.startswith("type of data"):
            rename[c] = "dest_data_type"
        elif c.startswith("notes of destination") or c == "notes":
            rename[c] = "dest_notes"
        elif c == "index":
            rename[c] = "index"
    df = df.rename(columns=rename)
    required = {"dest_code", "origin_code", "dest_name", "origin_name"}
    if not required <= set(df.columns):
        raise ValueError(f"missing expected columns {required - set(df.columns)}; got {list(df.columns)[:12]}")
    df.attrs["sheet"] = sheet
    df.attrs["header_row"] = h
    return df


def to_number(series: pd.Series) -> pd.Series:
    s = series.astype(object)
    s = s.where(~s.map(lambda v: str(v).strip() in MISSING_TOKENS), np.nan)
    s = s.map(lambda v: str(v).replace(",", "").replace(" ", "") if isinstance(v, str) else v)
    return pd.to_numeric(s, errors="coerce")


def tidy(df: pd.DataFrame, years: list[int] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (country-to-country long table, excluded-rows summary, report)."""
    year_cols = [c for c in df.columns if re.fullmatch(r"(both|male|female)_\d{4}", str(c))]
    if years is not None:
        year_cols = [c for c in year_cols if int(c.split("_")[1]) in years]
    rep_d, rep_o = HarmonizationReport("m49-dest"), HarmonizationReport("m49-origin")
    df = df.copy()
    df["dest_iso3"] = to_iso3(df["dest_code"], "m49", rep_d)
    df["origin_iso3"] = to_iso3(df["origin_code"], "m49", rep_o)
    keep = df["dest_iso3"].notna() & df["origin_iso3"].notna()
    excluded = (df.loc[~keep, ["dest_code", "dest_name", "origin_code", "origin_name"]]
                .astype(str).value_counts().reset_index(name="rows"))
    long = df.loc[keep, ["origin_iso3", "dest_iso3", "dest_data_type", "dest_notes", *year_cols]
                  if "dest_notes" in df.columns else ["origin_iso3", "dest_iso3", "dest_data_type", *year_cols]]
    long = long.melt(id_vars=[c for c in long.columns if c not in year_cols], value_vars=year_cols,
                     var_name="sex_year", value_name="stock_raw")
    long[["sex", "year"]] = long["sex_year"].str.split("_", expand=True)
    long["year"] = long["year"].astype(int)
    long["stock"] = to_number(long["stock_raw"])
    long["corridor_status"] = np.where(long["stock"].isna(), "missing", np.where(long["stock"] == 0, "reported_zero", "reported"))
    long = long.drop(columns=["sex_year", "stock_raw"])
    long["dest_data_type"] = long["dest_data_type"].fillna("").astype(str).str.strip()
    keys = ["origin_iso3", "dest_iso3", "dest_data_type", "year"]
    if long.duplicated(keys + ["sex"]).any():
        raise ValueError("duplicate corridor-sex-year rows in the workbook")
    wide = long.set_index(keys + ["sex"])["stock"].unstack("sex").reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={"both": "stock", "male": "stock_male", "female": "stock_female"})
    status = long[long["sex"] == "both"][["origin_iso3", "dest_iso3", "year", "corridor_status"]]
    wide = wide.merge(status, on=["origin_iso3", "dest_iso3", "year"], how="left")
    dup = wide.duplicated(["origin_iso3", "dest_iso3", "year"])
    if dup.any():
        raise ValueError(f"duplicate corridors after harmonization: {wide[dup].head()}")
    report = {"dest": rep_d, "origin": rep_o, "rows_in": len(df), "rows_country_pairs": int(keep.sum())}
    return wide, excluded, report


def destination_coverage(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Per destination: total migrant stock (origin 'World', M49 900) and the
    share attributed to identifiable countries; the remainder is aggregates,
    'Other' or unknown origins."""
    col = f"both_{year}"
    d = df.copy()
    d["value"] = to_number(d[col])
    d["dest_iso3"] = to_iso3(d["dest_code"], "m49")
    d["origin_iso3"] = to_iso3(d["origin_code"], "m49")
    world = d[pd.to_numeric(d["origin_code"], errors="coerce") == 900].groupby("dest_iso3")["value"].sum()
    attributed = d[d["origin_iso3"].notna()].groupby("dest_iso3")["value"].sum()
    out = pd.DataFrame({"total": world, "attributed_to_countries": attributed}).dropna(subset=["total"])
    out["attributed_share"] = out["attributed_to_countries"] / out["total"]
    types = d.drop_duplicates("dest_iso3").set_index("dest_iso3")["dest_data_type"] if "dest_data_type" in d else None
    if types is not None:
        out["dest_data_type"] = types
    return out.reset_index().rename(columns={"index": "dest_iso3"}).assign(year=year)
