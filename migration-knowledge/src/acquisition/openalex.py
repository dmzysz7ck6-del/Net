"""OpenAlex acquisition.

Strategy
--------
Downloading every international work would require millions of records. The
counting rules in ``cleaning/openalex.py`` can instead be computed exactly from
aggregate ``group_by`` queries:

1. For focal country X and window w, ``group_by=countries_distinct_count``
   gives the number of X's works with exactly k distinct countries.
2. For each k >= 2 present, ``group_by=authorships.countries`` restricted to
   ``countries_distinct_count:k`` gives, for every partner Y, the number of
   works with exactly k countries containing both X and Y.

Summing over k gives full counts; weighting by 1/C(k,2) gives fractional
counts exactly. Both directions (X's query and Y's query) are fetched, so
symmetry is a built-in validation check. Work-level records are downloaded
only for the focus origins to (a) validate the aggregate counts, (b) measure
pairs created solely by multi-affiliated authors (R8) and (c) check
duplicates.

Every response is cached on disk (resumable), every request is logged, and
per-country results are checkpointed to CSV. The API key and contact e-mail
are read from environment variables only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

import pandas as pd

from ..config import PATHS, load_config
from ..http import CachedClient
from .. import provenance


def _filter_string(filters: dict[str, str]) -> str:
    return ",".join(f"{k}:{v}" for k, v in filters.items())


def group_key(g: dict) -> str:
    """Normalize a group_by key: URLs -> last path segment; 'unknown' kept."""
    return str(g.get("key", "")).rstrip("/").rsplit("/", 1)[-1]


def int_key(g: dict) -> int | None:
    k = group_key(g)
    return int(k) if k.lstrip("-").isdigit() else None


class OpenAlex:
    def __init__(self, cache_dir: Path | None = None):
        cfg = load_config()
        self.cfg = cfg["openalex"]
        self.base = cfg["sources"]["openalex"]["base_url"].rstrip("/")
        self.mailto = os.environ.get(cfg["project"]["contact_env_var"])
        self.api_key = os.environ.get(cfg["project"]["api_key_env_var"])
        self.client = CachedClient(cache_dir or PATHS.raw / "openalex" / "cache", PATHS.request_log,
                                   requests_per_second=self.cfg["requests_per_second"],
                                   max_retries=self.cfg["max_retries"], backoff_base=self.cfg["backoff_base_seconds"])

    # -- low level -----------------------------------------------------------
    def _get(self, path: str, params: dict) -> dict:
        p = dict(params)
        if self.mailto:
            p["mailto"] = self.mailto
        secret = {"api_key": self.api_key} if self.api_key else None
        return self.client.get_json(f"{self.base}/{path}", p, secret_params=secret)

    def base_filters(self, years: tuple[int, int]) -> dict[str, str]:
        f = {k: str(v) for k, v in self.cfg["work_filters"].items()}
        f["publication_year"] = f"{years[0]}-{years[1]}" if years[0] != years[1] else str(years[0])
        return f

    def count(self, filters: dict[str, str]) -> int:
        return int(self._get("works", {"filter": _filter_string(filters), "per_page": 1, "select": "id"})["meta"]["count"])

    def group_by(self, filters: dict[str, str], field: str) -> list[dict]:
        """All groups for ``field`` (paginates with cursor when > per_page)."""
        groups: list[dict] = []
        cursor = "*"
        expected = None
        pages = 0
        while cursor:
            data = self._get("works", {"filter": _filter_string(filters), "group_by": field,
                                       "per_page": self.cfg["per_page"], "cursor": cursor})
            page = data.get("group_by") or []
            meta = data.get("meta") or {}
            if page and expected is None:
                expected = meta.get("groups_count")  # from the first non-empty page only
            groups.extend(page)
            pages += 1
            cursor = meta.get("next_cursor")
            if not page:
                break
        # If groups_count turns out to be a per-page figure (<= per_page) on a
        # multi-page result, completeness is instead established by the null cursor.
        if expected is not None and pages > 1 and int(expected) <= self.cfg["per_page"] and len(groups) > int(expected):
            expected = None
        if expected is not None and len(groups) != int(expected):
            raise RuntimeError(f"group_by {field} returned {len(groups)} groups but meta.groups_count={expected} "
                               f"(filters {filters}); refusing to continue with truncated groups")
        return groups

    def iterate_works(self, filters: dict[str, str], select: list[str]) -> Iterator[dict]:
        cursor = "*"
        while cursor:
            data = self._get("works", {"filter": _filter_string(filters), "per_page": self.cfg["per_page"],
                                       "cursor": cursor, "select": ",".join(select)})
            results = data.get("results") or []
            yield from results
            cursor = (data.get("meta") or {}).get("next_cursor")
            if not results:
                break

    # -- extraction tasks ------------------------------------------------------
    def country_k_table(self, iso2: str, years: tuple[int, int]) -> pd.DataFrame:
        base = self.base_filters(years) | {"authorships.countries": iso2}
        kdist = self.group_by(base, "countries_distinct_count")
        rows = []
        for g in kdist:
            k = int_key(g)
            if k is None or k < 2 or g["count"] == 0:
                continue
            partners = self.group_by(base | {"countries_distinct_count": str(k)}, "authorships.countries")
            # sum check: every work with k countries contributes k country-groups
            listed = sum(int(p["count"]) for p in partners if group_key(p).lower() != "unknown")
            for p in partners:
                code = group_key(p).upper()
                if code == "UNKNOWN":
                    continue
                rows.append({"focal": iso2.upper(), "partner": code, "k": k, "n_works": int(p["count"]),
                             "k_total_works": int(g["count"]), "sum_check": listed / (k * int(g["count"]))})
        return pd.DataFrame(rows, columns=["focal", "partner", "k", "n_works", "k_total_works", "sum_check"])

    def country_output(self, iso2: str, years: tuple[int, int]) -> dict:
        base = self.base_filters(years) | {"authorships.countries": iso2}
        kdist = {int_key(g): int(g["count"]) for g in self.group_by(base, "countries_distinct_count") if int_key(g) is not None}
        total = self.count(base)
        return {"iso2": iso2.upper(), "years": f"{years[0]}-{years[1]}", "articles": total,
                "intl_articles": sum(v for k, v in kdist.items() if k >= 2),
                "kdist": json.dumps(kdist, sort_keys=True)}

    def output_by_year(self, years: tuple[int, int]) -> pd.DataFrame:
        """Articles per country-year in one call per year (group_by authorships.countries)."""
        rows = []
        for y in range(years[0], years[1] + 1):
            for g in self.group_by(self.base_filters((y, y)), "authorships.countries"):
                code = group_key(g).upper()
                if code != "UNKNOWN":
                    rows.append({"iso2": code, "year": y, "articles": int(g["count"])})
        return pd.DataFrame(rows)

    def coverage(self, years: tuple[int, int]) -> pd.DataFrame:
        """Share of filtered works by number of distinct countries, per year
        (k = 0 means no usable country information)."""
        rows = []
        for y in range(years[0], years[1] + 1):
            base = self.base_filters((y, y))
            groups = self.group_by(base, "countries_distinct_count")
            for g in groups:
                k = int_key(g)
                rows.append({"year": y, "k": k if k is not None else -2, "works": int(g["count"])})
            # works with no country at all may be reported as an 'unknown' group or be absent
            total = self.count(base)
            rows.append({"year": y, "k": -1, "works": total})
        return pd.DataFrame(rows)


def extract_window(window_name: str, iso2_codes: list[str], *, out_dir: Path | None = None) -> pd.DataFrame:
    """Checkpointed extraction of per-k partner tables for many focal countries."""
    from ..config import window as get_window

    w = get_window(window_name)
    years = tuple(w["collab_years"])
    out_dir = out_dir or PATHS.raw / "openalex" / f"kpairs_{years[0]}_{years[1]}"
    out_dir.mkdir(parents=True, exist_ok=True)
    oa = OpenAlex()
    frames = []
    for code in iso2_codes:
        path = out_dir / f"{code.upper()}.csv"
        if path.exists():
            frames.append(pd.read_csv(path, keep_default_na=False, na_values=[""]))
            continue
        t = oa.country_k_table(code, years)
        t.to_csv(path, index=False)
        frames.append(t)
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    combined = out_dir.parent / f"kpairs_{years[0]}_{years[1]}.csv"
    df.to_csv(combined, index=False)
    provenance.record(combined, source=f"openalex_kpairs_{years[0]}_{years[1]}", url=oa.base + "/works",
                      license="CC0", rows=len(df),
                      params={"filters": oa.base_filters(years), "strategy": "group_by countries_distinct_count x authorships.countries",
                              "focal_countries": len(iso2_codes)})
    return df


def extract_outputs(years: tuple[int, int], iso2_codes: list[str]) -> pd.DataFrame:
    oa = OpenAlex()
    path = PATHS.raw / "openalex" / f"output_{years[0]}_{years[1]}.csv"
    done = pd.read_csv(path, keep_default_na=False) if path.exists() else pd.DataFrame(columns=["iso2"])
    rows = done.to_dict("records")
    have = set(done["iso2"]) if len(done) else set()
    for code in iso2_codes:
        if code.upper() in have:
            continue
        rows.append(oa.country_output(code, years))
        pd.DataFrame(rows).to_csv(path, index=False)  # checkpoint after each country
    df = pd.DataFrame(rows)
    provenance.record(path, source=f"openalex_output_{years[0]}_{years[1]}", url=oa.base + "/works",
                      license="CC0", rows=len(df), params={"filters": oa.base_filters(years)})
    return df


def extract_works(iso2: str, years: tuple[int, int]) -> Path:
    """Work-level records for a focus origin (international works only)."""
    oa = OpenAlex()
    path = PATHS.raw / "openalex" / "works" / f"{iso2.upper()}_{years[0]}_{years[1]}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.with_suffix(".done").exists():
        return path
    filters = oa.base_filters(years) | {"authorships.countries": iso2, "countries_distinct_count": ">1"}
    select = ["id", "publication_year", "type", "countries_distinct_count", "authorships", "primary_location"]
    n = 0
    with open(path, "w", encoding="utf-8") as fh:
        for w in oa.iterate_works(filters, select):
            slim = {"id": w.get("id"), "publication_year": w.get("publication_year"), "type": w.get("type"),
                    "countries_distinct_count": w.get("countries_distinct_count"),
                    "authorships": [{"countries": a.get("countries"),
                                     "institutions": [{"country_code": i.get("country_code")} for i in a.get("institutions") or []]}
                                    for a in w.get("authorships") or []]}
            fh.write(json.dumps(slim) + "\n")
            n += 1
    path.with_suffix(".done").write_text(str(n))
    provenance.record(path, source=f"openalex_works_{iso2}_{years[0]}_{years[1]}", url=oa.base + "/works",
                      license="CC0", rows=n, params={"filters": filters, "select": select})
    return path
