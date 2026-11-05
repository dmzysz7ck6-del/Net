"""Co-authorship counting rules (pure functions; tested on synthetic works).

Definitions
-----------
* A work's country set is the union of country codes over all its
  authorships (an author with institutions in two countries contributes both).
* Full counting: each distinct unordered international country pair present
  in a work receives 1, however many authors each country has.
* Fractional counting: a work with k distinct countries contributes
  1 / (k (k - 1) / 2) to each of its k (k - 1) / 2 pairs, so every
  international work carries a total weight of 1 across pairs.
* Inter-author counting (robustness R8): a pair (c1, c2) counts only if two
  *different* authors carry c1 and c2. Pairs that exist only because a single
  author lists affiliations in both countries are excluded.
* One OpenAlex work ID counts once: duplicate records are dropped by ID.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Iterable

import numpy as np
import pandas as pd


def short_id(x: str) -> str:
    return str(x).rstrip("/").rsplit("/", 1)[-1]


def author_countries(authorship: dict) -> set[str]:
    cs = set(c for c in (authorship.get("countries") or []) if c)
    for inst in authorship.get("institutions") or []:
        cc = inst.get("country_code")
        if cc:
            cs.add(cc)
    return {c.upper() for c in cs}


def work_countries_institutions_only(work: dict) -> set[str]:
    """Countries from matched institutions only (the API's countries_distinct_count
    may use this definition rather than authorships.countries; the validation
    computes k both ways)."""
    out: set[str] = set()
    for a in work.get("authorships") or []:
        for inst in a.get("institutions") or []:
            if inst.get("country_code"):
                out.add(inst["country_code"].upper())
    return out


def work_countries(work: dict) -> set[str]:
    out: set[str] = set()
    for a in work.get("authorships") or []:
        out |= author_countries(a)
    return out


def work_pairs(work: dict, mode: str = "any") -> set[tuple[str, str]]:
    if mode == "any":
        return set(combinations(sorted(work_countries(work)), 2))
    if mode == "inter_author":
        per_author = [author_countries(a) for a in work.get("authorships") or []]
        pairs: set[tuple[str, str]] = set()
        for i in range(len(per_author)):
            for j in range(len(per_author)):
                if i == j:
                    continue
                for c1 in per_author[i]:
                    for c2 in per_author[j]:
                        if c1 != c2:
                            pairs.add(tuple(sorted((c1, c2))))
        return pairs
    raise ValueError(mode)


def dedupe(works: Iterable[dict]) -> tuple[list[dict], int]:
    seen: set[str] = set()
    out, dups = [], 0
    for w in works:
        wid = short_id(w.get("id", ""))
        if wid in seen:
            dups += 1
            continue
        seen.add(wid)
        out.append(w)
    return out, dups


def count_pairs(works: Iterable[dict], mode: str = "any", max_countries: int | None = None) -> pd.DataFrame:
    """Full and fractional pair counts from work records (deduplicated by ID).

    The fractional weight always uses the work's full country set size k
    (not the inter-author subset), so the two modes are comparable."""
    works, _ = dedupe(works)
    full: dict[tuple[str, str], float] = defaultdict(float)
    frac: dict[tuple[str, str], float] = defaultdict(float)
    for w in works:
        k = len(work_countries(w))
        if k < 2 or (max_countries is not None and k > max_countries):
            continue
        weight = 1.0 / (k * (k - 1) / 2)
        for p in work_pairs(w, mode):
            full[p] += 1.0
            frac[p] += weight
    rows = [{"a": a, "b": b, "full": full[(a, b)], "frac": frac[(a, b)]} for (a, b) in sorted(full)]
    return pd.DataFrame(rows, columns=["a", "b", "full", "frac"])


def aggregate_k_table(k_table: pd.DataFrame, max_countries: int | None = None) -> pd.DataFrame:
    """Combine per-k partner counts from the group_by strategy.

    ``k_table`` columns: focal, partner, k, n_works, where n_works is the number
    of works with exactly k distinct countries that include both focal and
    partner (as returned by OpenAlex for the focal country's query). Returns
    one row per unordered pair with full and fractional counts and a
    ``symmetric_ok`` flag when both directions were queried and agree.
    """
    t = k_table[(k_table["k"] >= 2) & (k_table["focal"] != k_table["partner"])].copy()
    if max_countries is not None:
        t = t[t["k"] <= max_countries]
    t["w"] = 1.0 / (t["k"] * (t["k"] - 1) / 2)
    t["frac_part"] = t["n_works"] * t["w"]
    per_dir = t.groupby(["focal", "partner"], as_index=False).agg(full=("n_works", "sum"), frac=("frac_part", "sum"))
    lo = np.where(per_dir["focal"] < per_dir["partner"], per_dir["focal"], per_dir["partner"])
    hi = np.where(per_dir["focal"] < per_dir["partner"], per_dir["partner"], per_dir["focal"])
    per_dir = per_dir.assign(a=lo, b=hi, side=np.where(per_dir["focal"] == lo, "a", "b"))
    wide = per_dir.pivot_table(index=["a", "b"], columns="side", values=["full", "frac"], aggfunc="first")
    wide.columns = [f"{v}_{s}" for v, s in wide.columns]
    wide = wide.reset_index()
    for c in ["full_a", "full_b", "frac_a", "frac_b"]:
        if c not in wide:
            wide[c] = np.nan
    both = wide["full_a"].notna() & wide["full_b"].notna()
    wide["symmetric_ok"] = np.where(both, np.isclose(wide["full_a"], wide["full_b"]), np.nan)
    # Use the focal side when only one side was queried; when both were, they
    # must agree (checked in the data-quality report) and we average.
    wide["full"] = wide[["full_a", "full_b"]].mean(axis=1)
    wide["frac"] = wide[["frac_a", "frac_b"]].mean(axis=1)
    return wide[["a", "b", "full", "frac", "full_a", "full_b", "symmetric_ok"]]
