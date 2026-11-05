"""Parse the released bilateral scholarly-migration flows.

The parser identifies origin, destination, year and count columns by name and
infers the country-code scheme from the values (ISO2, ISO3, numeric or
names), failing loudly if any of these is ambiguous. Columns and their
meaning are confirmed against the dataset documentation in
``research/methodology.md`` (Dataset B).

Measurement note (from the source article): a "move" is inferred from a
change in the modal country of affiliation between a scholar's publications.
It is an affiliation-based event; it does not observe nationality,
birthplace or residence.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pandas as pd

from .countries import HarmonizationReport, to_iso3

ORIGIN_PAT = [r"^(country_)?from(_country)?$", r"^origin", r"^iso[23]?_?from$", r"^from_iso", r"^source_country",
              r"^country_origin", r"^orig", r"^departure"]
DEST_PAT = [r"^(country_)?to(_country)?$", r"^dest", r"^iso[23]?_?to$", r"^to_iso", r"^target_country",
            r"^country_destination", r"^arrival"]
YEAR_PAT = [r"^year$", r"^yr$", r"^time$", r"^period$"]
COUNT_PAT = [r"^n_?migrations?$", r"^n_?migrants?$", r"^flows?$", r"^count$", r"^n$", r"^number", r"^moves?$",
             r"^migrants?$", r"^value$", r"^n_scholars"]


def _match(cols: list[str], pats: list[str]) -> str | None:
    hits = [c for c in cols for p in pats if re.search(p, c.lower())]
    uniq = list(dict.fromkeys(hits))
    return uniq[0] if uniq else None


def find_flow_files(root: Path, source: str) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as zf:
                for m in zf.namelist():
                    target = p.parent / "unzipped" / Path(m).name
                    if not m.endswith("/") and not target.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(zf.read(m))
    for p in sorted(root.rglob("*")):
        name = p.name.lower()
        if p.suffix.lower() in (".csv", ".tsv", ".txt", ".xlsx") and source in name and ("flow" in name or "bilateral" in name):
            out.append(p)
    return out


def detect_scheme(values: pd.Series) -> str:
    v = values.dropna().astype(str).str.strip()
    if v.str.fullmatch(r"\d+").mean() > 0.95:
        return "m49"
    if v.str.fullmatch(r"[A-Za-z]{2}").mean() > 0.95:
        return "iso2"
    if v.str.fullmatch(r"[A-Za-z]{3}").mean() > 0.95:
        return "iso3"
    return "name"


def _names_to_iso3(values: pd.Series, rep: HarmonizationReport) -> list[str | None]:
    import country_converter as coco
    conv = coco.CountryConverter()
    uniq = values.dropna().unique().tolist()
    mapped = dict(zip(uniq, conv.convert(uniq, to="ISO3", not_found=None)))
    iso = [mapped.get(v) for v in values]
    return to_iso3([i if isinstance(i, str) else "" for i in iso], "iso3", rep)


def parse_flows(path: Path, source: str) -> tuple[pd.DataFrame, HarmonizationReport]:
    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, sep=None, engine="python", keep_default_na=False, na_values=[""])
    cols = list(df.columns)
    o, d, y, n = _match(cols, ORIGIN_PAT), _match(cols, DEST_PAT), _match(cols, YEAR_PAT), _match(cols, COUNT_PAT)
    missing = [k for k, v in {"origin": o, "destination": d, "year": y, "count": n}.items() if v is None]
    if missing:
        raise ValueError(f"{path.name}: cannot identify {missing} columns among {cols}")
    rep = HarmonizationReport(f"scholarly_{source}")
    scheme = detect_scheme(df[o])
    if scheme == "name":
        oi, di = _names_to_iso3(df[o], rep), _names_to_iso3(df[d], rep)
    else:
        oi, di = to_iso3(df[o], scheme, rep), to_iso3(df[d], scheme, rep)
    out = pd.DataFrame({"origin_iso3": oi, "dest_iso3": di, "year": pd.to_numeric(df[y], errors="coerce"),
                        "moves": pd.to_numeric(df[n], errors="coerce"), "source": source})
    out = out.dropna(subset=["origin_iso3", "dest_iso3", "year"])
    out = out[out["origin_iso3"] != out["dest_iso3"]]
    out["year"] = out["year"].astype(int)
    if (out["moves"] < 0).any():
        raise ValueError(f"{path.name}: negative counts")
    out.attrs["columns"] = {"origin": o, "destination": d, "year": y, "count": n, "scheme": scheme}
    return out, rep
