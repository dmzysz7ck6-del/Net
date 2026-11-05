"""Country-code harmonization (synthetic code lists; no research data)."""
from src.cleaning import countries as C


def test_crosswalk_keys_unique():
    cw = C.crosswalk()
    assert cw["iso3"].is_unique and cw["iso2"].is_unique
    assert {"KEN", "ETH", "SOM", "GHA", "TWN", "SSD"} <= set(cw["iso3"])


def test_m49_mapping_and_aggregates_reported():
    rep = C.HarmonizationReport("m49")
    out = C.to_iso3([404, "231", 706.0, 158, 830, 900, 947], "m49", rep)
    assert out[:4] == ["KEN", "ETH", "SOM", "TWN"]
    assert out[4] is None and "830" in rep.excluded          # Channel Islands: explicit exclusion
    assert out[5] is None and out[6] is None                 # World / SSA aggregates: unmatched
    assert set(rep.unmatched) == {"900", "947"}


def test_openalex_iso2_urls_and_kosovo():
    rep = C.HarmonizationReport("iso2")
    out = C.to_iso3(["https://openalex.org/countries/KE", "et", "XK", "ZZ"], "iso2", rep)
    assert out[:2] == ["KEN", "ETH"]
    assert out[2] is None and "XK" in rep.excluded
    assert out[3] is None and rep.unmatched == {"ZZ": 1}


def test_cepii_legacy_codes():
    rep = C.HarmonizationReport("cepii")
    out = C.to_iso3(["ROM", "ZAR", "TMP", "PAL", "YUG", "KEN"], "cepii", rep)
    assert out == ["ROU", "COD", "TLS", "PSE", None, "KEN"]
    assert rep.split["YUG"] == ["SRB", "MNE"]


def test_wdi_kosovo_excluded_even_via_iso3():
    rep = C.HarmonizationReport("iso3")
    assert C.to_iso3(["XKX"], "iso3", rep) == [None]


def test_ssa_flag_follows_m49():
    cw = C.crosswalk().set_index("iso3")
    assert cw.loc["KEN", "ssa"] and cw.loc["NGA", "ssa"] and cw.loc["ZAF", "ssa"]
    assert not cw.loc["EGY", "ssa"] and not cw.loc["SDN", "ssa"]  # M49: Sudan is Northern Africa
