"""Co-authorship counting rules on synthetic work records."""
import pandas as pd
import pytest

from src.cleaning import openalex as O


def W(wid, *authors):
    return {"id": f"https://openalex.org/{wid}",
            "authorships": [{"countries": list(a), "institutions": [{"country_code": c} for c in a]} for a in authors]}


WORKS = [
    W("W1", ["KE"], ["KE"], ["US"]),            # many KE authors: KE-US counted once
    W("W2", ["KE"], ["US"], ["GB"]),            # k=3 -> 3 pairs, frac 1/3 each
    W("W3", ["KE", "US"]),                      # single author, two affiliations
    W("W1", ["KE"], ["US"]),                    # duplicate record of W1
    W("W4", ["KE"], ["KE"]),                    # domestic only
    W("W5", ["ET"], [], ["KE"]),                # author without affiliation
]


def test_dedupe_by_work_id():
    works, dups = O.dedupe(WORKS)
    assert dups == 1 and len(works) == 5


def test_full_and_fractional_counting():
    c = O.count_pairs(WORKS).set_index(["a", "b"])
    assert c.loc[("KE", "US"), "full"] == 3                      # W1, W2, W3
    assert c.loc[("KE", "US"), "frac"] == pytest.approx(1 + 1 / 3 + 1)
    assert c.loc[("GB", "KE"), "full"] == 1 and c.loc[("GB", "KE"), "frac"] == pytest.approx(1 / 3)
    assert c.loc[("ET", "KE"), "full"] == 1
    assert ("KE", "KE") not in c.index
    # each international work carries total fractional weight 1
    assert c["frac"].sum() == pytest.approx(4)                   # W1, W2, W3, W5


def test_inter_author_excludes_single_author_coaffiliation():
    c = O.count_pairs(WORKS, mode="inter_author").set_index(["a", "b"])
    assert c.loc[("KE", "US"), "full"] == 2                      # W3 dropped


def test_mega_collaboration_exclusion():
    c = O.count_pairs(WORKS, max_countries=2).set_index(["a", "b"])
    assert ("GB", "KE") not in c.index


def test_k_table_aggregation_matches_direct_counting():
    works, _ = O.dedupe(WORKS)
    rows = []
    for focal in ["KE", "US", "GB", "ET"]:
        for w in works:
            cs = O.work_countries(w)
            if focal not in cs or len(cs) < 2:
                continue
            for p in cs:
                rows.append({"focal": focal, "partner": p, "k": len(cs)})
    kt = pd.DataFrame(rows).groupby(["focal", "partner", "k"]).size().rename("n_works").reset_index()
    agg = O.aggregate_k_table(kt).set_index(["a", "b"]).sort_index()
    direct = O.count_pairs(works).set_index(["a", "b"]).sort_index()
    assert agg["symmetric_ok"].all()
    pd.testing.assert_series_equal(agg["full"], direct["full"], check_names=False)
    pd.testing.assert_series_equal(agg["frac"], direct["frac"], check_names=False)


def test_openalex_url_ids():
    assert O.short_id("https://openalex.org/W123") == "W123"
