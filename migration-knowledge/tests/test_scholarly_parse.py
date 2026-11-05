"""Scholarly-flow parser on synthetic files with different column conventions."""
import pandas as pd
import pytest

from src.cleaning import scholarly as S


@pytest.mark.parametrize("cols,codes", [
    (("iso2_from", "iso2_to", "year", "n_migrations"), ("KE", "US")),
    (("origin", "destination", "year", "count"), ("KEN", "USA")),
    (("country_from", "country_to", "year", "flow"), ("Kenya", "United States")),
])
def test_parse_variants(tmp_path, cols, codes):
    o, d, y, n = cols
    df = pd.DataFrame({o: [codes[0], codes[1], codes[0]], d: [codes[1], codes[0], codes[0]], y: [2012, 2013, 2012], n: [5, 2, 9]})
    p = tmp_path / "openalex_bilateral_flows.csv"
    df.to_csv(p, index=False)
    out, rep = S.parse_flows(p, "openalex")
    assert len(out) == 2                                  # self-flow dropped
    r = out[(out.origin_iso3 == "KEN") & (out.dest_iso3 == "USA")].iloc[0]
    assert r.moves == 5 and r.year == 2012 and r.source == "openalex"


def test_ambiguous_columns_fail(tmp_path):
    p = tmp_path / "openalex_flows.csv"
    pd.DataFrame({"a": ["KE"], "b": ["US"], "c": [1]}).to_csv(p, index=False)
    with pytest.raises(ValueError):
        S.parse_flows(p, "openalex")


def test_find_flow_files(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "scopus_2024_V1_flows.csv").write_text("a\n")
    (tmp_path / "x" / "openalex_country_level.csv").write_text("a\n")
    assert [p.name for p in S.find_flow_files(tmp_path, "scopus")] == ["scopus_2024_V1_flows.csv"]
    assert S.find_flow_files(tmp_path, "openalex") == []
