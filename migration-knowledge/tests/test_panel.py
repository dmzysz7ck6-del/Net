"""Temporal alignment and regression-input integrity."""
import numpy as np
import pandas as pd
import pytest

from src.cleaning import panel as P
from src.config import window


def small_inputs():
    U = ["ETH", "KEN", "USA"]
    mig = pd.DataFrame({"origin_iso3": ["KEN", "ETH", "ETH"], "dest_iso3": ["USA", "USA", "KEN"],
                        "year": [2015] * 3, "stock": [100.0, 200.0, 50.0]})
    mob = pd.DataFrame({"origin_iso3": ["KEN", "USA"], "dest_iso3": ["USA", "KEN"], "year": [2011, 2013],
                        "moves": [5.0, 2.0]})
    col = pd.DataFrame({"a": ["ETH", "KEN"], "b": ["USA", "USA"], "full": [10.0, 30.0], "frac": [8.0, 25.0]})
    geo = pd.DataFrame({"a": ["ETH", "ETH", "KEN"], "b": ["KEN", "USA", "USA"], "distw": [1000.0, 11000.0, 12000.0],
                        "contig": [1, 0, 0], "comlang_off": [0, 0, 1], "colony": [0, 0, 0], "comcol": [0, 0, 0]})
    out = pd.DataFrame({"iso3": U, "articles": [500.0, 900.0, 1e6]})
    return U, mig, mob, col, geo, out


def test_primary_window_definition():
    w = window("primary")
    assert w["migrant_stock_year"] == 2015 and w["mobility_years"] == [2010, 2014] and w["collab_years"] == [2015, 2019]
    assert w["mobility_years"][1] < w["collab_years"][0]  # lagged design


def test_alignment_check_rejects_wrong_years():
    U, mig, mob, col, geo, out = small_inputs()
    w = window("primary")
    P.check_alignment(w, mig, mob, (2015, 2019))
    with pytest.raises(ValueError):
        P.check_alignment(w, mig.assign(year=2020), mob, (2015, 2019))
    with pytest.raises(ValueError):
        P.check_alignment(w, mig, mob.assign(year=2016), (2015, 2019))
    with pytest.raises(ValueError):
        P.check_alignment(w, mig, mob, (2010, 2014))


def test_dyads_integrity_and_direction():
    U, mig, mob, col, geo, out = small_inputs()
    d = P.build_dyads(U, mig, mob, col, geo, out)
    assert P.validate_dyads(d) == []
    r = d.set_index(["a", "b"]).loc[("KEN", "USA")]
    assert r.mig_ab == 100 and r.mig_ba == 0 and r.mob_ab == 5 and r.mob_ba == 2
    assert r.low == "KEN" and r.mob_up == 5 and r.mob_down == 2
    e = d.set_index(["a", "b"]).loc[("ETH", "KEN")]
    assert e.full == 0 and e.mig_ab == 50 and e.ln_mig == pytest.approx(np.log(51))
    assert e.low == "ETH" and e.mig_up == 50


def test_validate_detects_problems():
    U, mig, mob, col, geo, out = small_inputs()
    d = P.build_dyads(U, mig, mob, col, geo, out)
    bad = pd.concat([d, d.iloc[[0]]])
    assert any("duplicate" in p for p in P.validate_dyads(bad))
    bad2 = d.assign(frac=d["full"] + 1)
    assert any("fractional" in p for p in P.validate_dyads(bad2))
