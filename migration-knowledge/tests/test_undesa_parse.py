"""UN DESA workbook parsing on a small synthetic workbook that mimics the
published layout (title rows, merged sex super-header, aggregates)."""
import numpy as np
import pandas as pd
import pytest

from src.cleaning import undesa as U

YEARS = [2010, 2015, 2020]


def make_workbook(path):
    header = ["Index", "Region, development group, country or area of destination", "Notes of destination",
              "Location code of destination", "Type of data of destination",
              "Region, development group, country or area of origin", "Location code of origin"]
    sexhdr = [None] * len(header) + ["Both sexes"] + [None] * 2 + ["Male"] + [None] * 2 + ["Female"] + [None] * 2
    hdr = header + YEARS * 3
    rows = [
        ["United Nations", None], ["International migrant stock 2024"], [], sexhdr, hdr,
        # destination Kenya (404): born in Somalia (706), Ethiopia (231), Other (2003), World (900)
        [1, "Kenya", None, 404, "B R", "World", 900, 1000, 1100, 1200, 600, 650, 700, 400, 450, 500],
        [2, "Kenya", None, 404, "B R", "Somalia", 706, 300, 400, 500, 160, 210, 260, 140, 190, 240],
        [3, "Kenya", None, 404, "B R", "Ethiopia", 231, "..", 0, 50, "..", 0, 25, "..", 0, 25],
        [4, "Kenya", None, 404, "B R", "Other", 2003, 10, 10, 10, 5, 5, 5, 5, 5, 5],
        # destination United Kingdom (826): born in Kenya
        [5, "United Kingdom", None, 826, "B", "Kenya", 404, 140000, 139000, 138000, 70000, 69000, 68000, 70000, 70000, 70000],
        # aggregate destination (Sub-Saharan Africa, 947) must be excluded
        [6, "Sub-Saharan Africa", None, 947, None, "Somalia", 706, 9, 9, 9, 4, 4, 4, 5, 5, 5],
    ]
    pd.DataFrame(rows).to_excel(path, sheet_name="Table 1", header=False, index=False)


@pytest.fixture
def table(tmp_path):
    p = tmp_path / "ims.xlsx"
    make_workbook(p)
    return U.read_table(p)


def test_header_and_columns_detected(table):
    assert {"dest_code", "origin_code", "dest_data_type", "both_2015", "male_2020", "female_2010"} <= set(table.columns)


def test_orientation_origin_to_destination(table):
    long, excluded, rep = U.tidy(table)
    r = long[(long.origin_iso3 == "SOM") & (long.dest_iso3 == "KEN") & (long.year == 2015)].iloc[0]
    assert r.stock == 400 and r.stock_male == 210 and r.stock_female == 190
    k = long[(long.origin_iso3 == "KEN") & (long.dest_iso3 == "GBR") & (long.year == 2010)].iloc[0]
    assert k.stock == 140000
    assert not ((long.origin_iso3 == "KEN") & (long.dest_iso3 == "SOM")).any()


def test_missing_vs_zero(table):
    long, _, _ = U.tidy(table)
    eth = long[(long.origin_iso3 == "ETH") & (long.dest_iso3 == "KEN")].set_index("year")
    assert np.isnan(eth.loc[2010, "stock"]) and eth.loc[2010, "corridor_status"] == "missing"
    assert eth.loc[2015, "stock"] == 0 and eth.loc[2015, "corridor_status"] == "reported_zero"
    assert eth.loc[2020, "corridor_status"] == "reported"


def test_aggregates_and_other_excluded_and_reported(table):
    long, excluded, rep = U.tidy(table)
    assert set(long.dest_iso3) == {"KEN", "GBR"}
    assert set(long.origin_iso3) == {"SOM", "ETH", "KEN"}
    assert "900" in rep["origin"].unmatched and "2003" in rep["origin"].unmatched
    assert "947" in rep["dest"].unmatched


def test_destination_coverage(table):
    cov = U.destination_coverage(table, 2015).set_index("dest_iso3")
    assert cov.loc["KEN", "total"] == 1100
    assert cov.loc["KEN", "attributed_share"] == pytest.approx(400 / 1100)
