"""build_collab: per-k OpenAlex tables -> processed pair counts (Namibia's ISO2
code 'NA' must survive CSV round-trips; Kosovo must be excluded)."""
import pandas as pd
import pytest

from src.config import PATHS


@pytest.fixture
def root(tmp_path):
    old = PATHS.root
    PATHS.set_root(tmp_path); PATHS.ensure()
    yield tmp_path
    PATHS.set_root(old)


def test_build_collab_namibia_and_kosovo(root):
    from src.cleaning.build import build_collab
    d = PATHS.raw / "openalex"; d.mkdir(parents=True, exist_ok=True)
    kt = pd.DataFrame([
        # Namibia (NA) - South Africa (ZA): 3 works with k=2, 1 with k=3 (with XK)
        {"focal": "NA", "partner": "NA", "k": 2, "n_works": 3}, {"focal": "NA", "partner": "ZA", "k": 2, "n_works": 3},
        {"focal": "NA", "partner": "NA", "k": 3, "n_works": 1}, {"focal": "NA", "partner": "ZA", "k": 3, "n_works": 1},
        {"focal": "NA", "partner": "XK", "k": 3, "n_works": 1},
        {"focal": "ZA", "partner": "NA", "k": 2, "n_works": 3}, {"focal": "ZA", "partner": "NA", "k": 3, "n_works": 1},
    ])
    kt.to_csv(d / "kpairs_2015_2019.csv", index=False)
    pd.DataFrame({"iso2": ["NA", "ZA"], "years": ["2015-2019"] * 2, "articles": [100, 5000],
                  "intl_articles": [60, 2000], "kdist": ["{}", "{}"]}).to_csv(d / "output_2015_2019.csv", index=False)
    build_collab()
    c = pd.read_csv(PATHS.processed / "collab_2015_2019.csv", keep_default_na=False, na_values=[""])
    r = c[(c.a == "NAM") & (c.b == "ZAF")].iloc[0]
    assert r.full == 4 and r.frac == pytest.approx(3 + 1 / 3)
    assert r.full_nomega == 4                                    # k <= 20
    assert "XKX" not in set(c.a) | set(c.b)
    o = pd.read_csv(PATHS.processed / "output_2015_2019.csv", keep_default_na=False, na_values=[""])
    assert set(o.iso3) == {"NAM", "ZAF"}
    h = pd.read_csv(PATHS.tables / "harmonization_openalex_2015_2019.csv")
    assert "XK" in set(h["code"])
