"""Country-code harmonization.

Every source uses a different geography key:

* UN DESA International Migrant Stock: UN M49 numeric location codes, mixed
  with regional/income aggregates and residual "Other" origins.
* OpenAlex: ISO 3166-1 alpha-2 (plus ``XK`` for Kosovo).
* CEPII GeoDist: ISO alpha-3 with legacy codes (ROM, ZAR, TMP, PAL, YUG, ANT).
* World Bank WDI: ISO alpha-3 plus World-Bank-specific codes (XKX, CHI) and
  aggregates.
* Scholarly migration data: country codes as released (resolved at parse time).

The canonical key is ISO 3166-1 alpha-3 (``iso3``). Ambiguous entities are
never merged silently: each one has an explicit entry in ``SPECIAL_CASES``
with the decision and the reason, and every unmatched code is reported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable

import pandas as pd

# Decisions for entities whose mapping is not one-to-one or not ISO standard.
# action: "map" (to iso3), "exclude" (drop, report), "split" (copy values to
# several iso3 codes, flagged as imputed; used only for covariates).
SPECIAL_CASES: dict[tuple[str, str], dict] = {
    # CEPII legacy codes
    ("cepii", "ROM"): {"action": "map", "iso3": "ROU", "reason": "legacy ISO3 for Romania"},
    ("cepii", "ZAR"): {"action": "map", "iso3": "COD", "reason": "legacy code for DR Congo (Zaire)"},
    ("cepii", "TMP"): {"action": "map", "iso3": "TLS", "reason": "legacy code for Timor-Leste"},
    ("cepii", "PAL"): {"action": "map", "iso3": "PSE", "reason": "CEPII code for Palestine"},
    ("cepii", "YUG"): {"action": "split", "iso3": ["SRB", "MNE"],
                        "reason": "GeoDist predates the 2006 Serbia/Montenegro split; geography copied to both, flagged geo_imputed"},
    ("cepii", "ANT"): {"action": "split", "iso3": ["CUW", "SXM", "BES"],
                        "reason": "Netherlands Antilles dissolved 2010; geography copied, flagged geo_imputed"},
    # OpenAlex / WDI Kosovo: UN DESA reports Kosovo inside Serbia, so a separate
    # Kosovo node cannot be aligned across layers. Excluded and reported.
    ("iso2", "XK"): {"action": "exclude", "reason": "Kosovo not separately reported by UN DESA (included in Serbia)"},
    ("wdi", "XKX"): {"action": "exclude", "reason": "Kosovo not separately reported by UN DESA (included in Serbia)"},
    # Channel Islands: UN M49 830 aggregates Jersey (JEY) and Guernsey (GGY).
    ("m49", "830"): {"action": "exclude", "reason": "Channel Islands aggregate (no single ISO3); population < threshold"},
    ("wdi", "CHI"): {"action": "exclude", "reason": "Channel Islands aggregate (no single ISO3)"},
    # Taiwan has M49 158 but no UN 'UNcode' in some tables; map explicitly.
    ("m49", "158"): {"action": "map", "iso3": "TWN", "reason": "UN DESA 'China, Taiwan Province of China'"},
    # Sudan before 2011 is M49 736 in some historical tables.
    ("m49", "736"): {"action": "exclude", "reason": "former Sudan (pre-2011) code; not used in the 2024 revision for 2010+"},
    # Netherlands Antilles in some legacy M49 tables
    ("m49", "530"): {"action": "exclude", "reason": "former Netherlands Antilles"},
}


@dataclass
class HarmonizationReport:
    scheme: str
    matched: int = 0
    unmatched: dict[str, int] = field(default_factory=dict)
    excluded: dict[str, str] = field(default_factory=dict)
    split: dict[str, list[str]] = field(default_factory=dict)

    def as_frame(self) -> pd.DataFrame:
        rows = [{"scheme": self.scheme, "code": c, "status": "unmatched", "n": n, "detail": ""}
                for c, n in self.unmatched.items()]
        rows += [{"scheme": self.scheme, "code": c, "status": "excluded", "n": None, "detail": r}
                 for c, r in self.excluded.items()]
        rows += [{"scheme": self.scheme, "code": c, "status": "split", "n": None, "detail": ",".join(v)}
                 for c, v in self.split.items()]
        return pd.DataFrame(rows, columns=["scheme", "code", "status", "n", "detail"])


@lru_cache(maxsize=1)
def crosswalk() -> pd.DataFrame:
    """Canonical country table keyed by ISO3.

    Columns: iso3, iso2, m49, name, subregion (UN M49 subregion), continent,
    ssa (UN M49 Sub-Saharan Africa: Africa excluding 'Northern Africa'),
    un_member (bool).
    """
    import country_converter as coco

    df = coco.CountryConverter().data
    out = pd.DataFrame({
        "iso3": df["ISO3"].astype(str),
        "iso2": df["ISO2"].astype(str),
        "m49": pd.to_numeric(df["ISOnumeric"], errors="coerce").astype("Int64"),
        "name": df["name_short"].astype(str),
        "subregion": df["UNregion"].astype(str),
        "continent": df["continent"].astype(str),
        "un_member": df["UNmember"].notna(),
    })
    # Kosovo has no ISO 3166-1 numeric/M49 code of its own in UN statistics.
    out.loc[out.iso3 == "XKX", "m49"] = pd.NA
    out["ssa"] = (out["continent"] == "Africa") & (out["subregion"] != "Northern Africa")
    out = out.drop_duplicates("iso3").sort_values("iso3").reset_index(drop=True)
    if out["iso3"].duplicated().any() or out["iso2"].duplicated().any():  # pragma: no cover
        raise ValueError("crosswalk keys are not unique")
    return out


def _lookup(scheme: str) -> dict[str, str]:
    cw = crosswalk()
    if scheme == "iso3" or scheme == "wdi" or scheme == "cepii":
        return {c: c for c in cw["iso3"]}
    if scheme == "iso2":
        return dict(zip(cw["iso2"], cw["iso3"]))
    if scheme == "m49":
        sub = cw.dropna(subset=["m49"])
        return {str(int(m)): i for m, i in zip(sub["m49"], sub["iso3"])}
    raise ValueError(f"unknown scheme {scheme!r}")


def normalize_code(code, scheme: str) -> str:
    if code is None or (isinstance(code, float) and pd.isna(code)):
        return ""
    s = str(code).strip()
    if scheme == "m49":
        try:
            return str(int(float(s)))
        except ValueError:
            return s
    if scheme == "iso2" and s.startswith("http"):
        s = s.rstrip("/").rsplit("/", 1)[-1]  # OpenAlex group keys are URLs
    return s.upper()


def to_iso3(codes: Iterable, scheme: str, report: HarmonizationReport | None = None) -> list[str | None]:
    """Map codes to ISO3. Excluded/unmatched codes map to ``None`` and are
    recorded in ``report``. Split codes are rejected here (use
    :func:`expand_split` for covariate tables)."""
    table = _lookup(scheme)
    out: list[str | None] = []
    for raw in codes:
        code = normalize_code(raw, scheme)
        special = SPECIAL_CASES.get((scheme, code))
        if special is not None:
            if special["action"] == "map":
                out.append(special["iso3"])
                if report: report.matched += 1
                continue
            if special["action"] == "exclude":
                out.append(None)
                if report: report.excluded[code] = special["reason"]
                continue
            if special["action"] == "split":
                out.append(None)
                if report: report.split[code] = list(special["iso3"])
                continue
        iso3 = table.get(code)
        if iso3 is not None and (scheme, code) not in SPECIAL_CASES:
            # entity-level exclusions apply whatever the source scheme
            if ("iso2", _iso2_of(iso3)) in SPECIAL_CASES and SPECIAL_CASES[("iso2", _iso2_of(iso3))]["action"] == "exclude":
                out.append(None)
                if report: report.excluded[code] = SPECIAL_CASES[("iso2", _iso2_of(iso3))]["reason"]
                continue
            out.append(iso3)
            if report: report.matched += 1
        else:
            out.append(None)
            if report: report.unmatched[code] = report.unmatched.get(code, 0) + 1
    return out


def _iso2_of(iso3: str) -> str:
    cw = crosswalk()
    m = cw.loc[cw.iso3 == iso3, "iso2"]
    return m.iloc[0] if len(m) else ""


def expand_split(df: pd.DataFrame, col: str, scheme: str = "cepii") -> pd.DataFrame:
    """Return rows for split codes duplicated onto their successor ISO3 codes
    with ``<col>_imputed = True``. Used for geography covariates only."""
    rows = []
    for (sch, code), spec in SPECIAL_CASES.items():
        if sch != scheme or spec["action"] != "split":
            continue
        sub = df[df[col].astype(str).str.upper() == code]
        for succ in spec["iso3"]:
            rows.append(sub.assign(**{col: succ, f"{col}_imputed": True}))
    return pd.concat(rows, ignore_index=True) if rows else df.iloc[0:0].assign(**{f"{col}_imputed": True})


def iso3_to_iso2(iso3: str) -> str:
    return _iso2_of(iso3)


def name(iso3: str) -> str:
    cw = crosswalk()
    m = cw.loc[cw.iso3 == iso3, "name"]
    return m.iloc[0] if len(m) else iso3


def special_cases_frame() -> pd.DataFrame:
    rows = []
    for (scheme, code), spec in SPECIAL_CASES.items():
        target = spec.get("iso3", "")
        rows.append({"scheme": scheme, "code": code, "action": spec["action"],
                     "target": ",".join(target) if isinstance(target, list) else target,
                     "reason": spec["reason"]})
    return pd.DataFrame(rows)
