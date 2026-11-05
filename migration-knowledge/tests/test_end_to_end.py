"""End-to-end plumbing on a SYNTHETIC processed-data fixture written to a tmp
directory. Verifies that the analysis and figure code run and produce their
declared outputs; the numbers have no research meaning."""
import copy

import numpy as np
import pandas as pd
import pytest

from src import config as CFG
from src.config import PATHS, load_config

ISO = ["KEN", "ETH", "SOM", "GHA", "NGA", "UGA", "TZA", "RWA", "SEN", "ZAF", "USA", "GBR", "FRA", "DEU",
       "CHN", "IND", "CAN", "NLD", "SWE", "BEL", "ITA", "SAU", "ARE", "BRA", "JPN", "EGY"]


def make_fixture(root, seed=0):
    rng = np.random.default_rng(seed)
    n = len(ISO)
    size = rng.lognormal(0, 1.2, n)
    coords = pd.DataFrame({"iso3": ISO, "lat": rng.uniform(-35, 60, n), "lon": rng.uniform(-100, 140, n)})
    D = np.sqrt((coords.lat.values[:, None] - coords.lat.values[None]) ** 2 + (coords.lon.values[:, None] - coords.lon.values[None]) ** 2) * 111 + 50
    aff = rng.normal(0, 1, (n, n)); aff = (aff + aff.T) / 2
    proc = root / "data" / "processed"; proc.mkdir(parents=True)
    mig, mob = [], []
    for y in (2010, 2015, 2020):
        M = rng.poisson(5e4 * np.outer(size, size) * np.exp(aff) / (D / 1000))
        for i in range(n):
            for j in range(n):
                if i != j and M[i, j] > 0:
                    mig.append({"origin_iso3": ISO[i], "dest_iso3": ISO[j], "year": y, "stock": float(M[i, j]),
                                "dest_data_type": "B", "corridor_status": "reported"})
    for y in range(2005, 2021):
        S = rng.poisson(0.5 * np.outer(size, size) * np.exp(aff))
        for i in range(n):
            for j in range(n):
                if i != j and S[i, j] > 0:
                    for src in ("openalex", "scopus"):
                        mob.append({"origin_iso3": ISO[i], "dest_iso3": ISO[j], "year": y, "moves": float(S[i, j]), "source": src})
    pd.DataFrame(mig).to_csv(proc / "migration_stocks.csv", index=False)
    pd.DataFrame(mob).to_csv(proc / "scholarly_moves.csv", index=False)
    for y0, y1 in [(2010, 2014), (2015, 2019), (2020, 2024), (2005, 2009)]:
        rows = []
        Cm = rng.poisson(20 * np.outer(size, size) * np.exp(0.5 * aff) / (D / 1000) ** 0.5)
        for i in range(n):
            for j in range(i + 1, n):
                rows.append({"a": min(ISO[i], ISO[j]), "b": max(ISO[i], ISO[j]), "full": float(Cm[i, j]),
                             "frac": float(Cm[i, j]) * 0.6, "full_nomega": float(round(Cm[i, j] * 0.9)), "frac_nomega": float(Cm[i, j]) * 0.55})
        pd.DataFrame(rows).to_csv(proc / f"collab_{y0}_{y1}.csv", index=False)
        pd.DataFrame({"iso3": ISO, "articles": (size * 1e4).round(), "intl_articles": (size * 3e3).round()}).to_csv(proc / f"output_{y0}_{y1}.csv", index=False)
        pd.DataFrame({"iso3": ISO, "intl_articles": (size * 3e3).round()}).to_csv(proc / f"collab_{y0}_{y1}_nodes.csv", index=False)
    wdi = pd.DataFrame([{"iso3": c, "year": y, "population": float(size[i] * 3e7), "gdp_pc_ppp_const": float(rng.lognormal(9, 1)),
                         "income_id": "HIC" if c in ("USA", "GBR", "FRA", "DEU", "CAN", "NLD", "SWE", "BEL", "ITA", "SAU", "ARE", "JPN") else "LMC"}
                        for i, c in enumerate(ISO) for y in range(2005, 2025)])
    wdi.to_csv(proc / "wdi_panel.csv", index=False)
    geo = []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = sorted((ISO[i], ISO[j]))
            geo.append({"a": a, "b": b, "distw": D[i, j], "dist": D[i, j] * 1.05, "contig": int(D[i, j] < 2500),
                        "comlang_off": int(rng.random() < 0.15), "comlang_ethno": int(rng.random() < 0.2),
                        "colony": int(rng.random() < 0.05), "comcol": int(rng.random() < 0.08), "geo_imputed": False})
    pd.DataFrame(geo).to_csv(proc / "geo_dyads.csv", index=False)
    coords.to_csv(proc / "country_coords.csv", index=False)


@pytest.fixture
def fixture_root(tmp_path):
    old_root = PATHS.root
    cfg = load_config()
    saved = copy.deepcopy(cfg)
    cfg["alignment"].update({"null_draws": 50, "bootstrap_draws": 20, "min_origin_emigrants": 1, "min_origin_intl_papers": 1})
    cfg["topology"].update({"null_draws": 10, "betweenness_null_draws": 5, "community_null_draws": 5})
    cfg["gravity"].update({"cv_folds": 3})
    make_fixture(tmp_path)
    PATHS.set_root(tmp_path)
    PATHS.ensure()
    yield tmp_path
    PATHS.set_root(old_root)
    cfg.clear(); cfg.update(saved)


def test_run_window_and_figures(fixture_root):
    from src.analysis import run
    from src.visualization import make
    s = run.run_window("primary", robustness=True)
    assert s["n_countries"] == len(ISO)
    t = PATHS.tables
    for f in ["alignment_primary.csv", "gravity_primary.csv", "gravity_cv_primary.csv", "residuals_primary.csv",
              "topology_primary.csv", "bridges_primary.csv", "universe_primary.csv", "jackknife_primary.csv"]:
        assert (t / f).exists(), f
    g = pd.read_csv(t / "gravity_primary.csv")
    assert {"M1", "M2", "M3"} <= set(g["model"])
    paths = make.make_figures(windows=["primary"])
    assert len(paths) >= 10 and all(p.exists() and p.stat().st_size > 0 for p in paths)


def test_comparators_rule_is_outcome_blind_and_non_african(fixture_root):
    from src.analysis import run
    from src.cleaning import countries as C
    wd = run.load_window("primary")
    comp = run.comparison_origins(wd, ["KEN", "ETH"], 2)
    assert len(comp) == 4
    cont = C.crosswalk().set_index("iso3")["continent"]
    assert all(cont[c] != "Africa" for c in comp["comparator"])
    # depends only on WDI covariates: changing collaboration data must not change it
    import pandas as pd
    col = pd.read_csv(PATHS.processed / "collab_2015_2019.csv")
    col["full"] = col["full"][::-1].to_numpy()
    col["frac"], col["full_nomega"], col["frac_nomega"] = col["full"] * 0.6, (col["full"] * 0.9).round(), col["full"] * 0.55
    col.to_csv(PATHS.processed / "collab_2015_2019.csv", index=False)
    comp2 = run.comparison_origins(run.load_window("primary"), ["KEN", "ETH"], 2)
    assert comp["comparator"].tolist() == comp2["comparator"].tolist()


def test_case_study_rule(fixture_root):
    import pandas as pd
    from src.visualization.make import choose_case_studies
    pd.DataFrame({"origin": ["KEN", "ETH", "GHA"], "jsd_raw": [0.2, 0.6, 0.4]}).to_csv(PATHS.tables / "alignment_primary.csv", index=False)
    pd.DataFrame({"origin": ["KEN", "ETH", "GHA"], "jsd_raw": [0.25, 0.5, 0.45]}).to_csv(PATHS.tables / "alignment_primary_frac.csv", index=False)
    assert choose_case_studies(["KEN", "ETH", "GHA"]) == ["ETH", "KEN"]
