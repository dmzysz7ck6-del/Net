"""Generate all figures (static SVG/PNG and interactive HTML) from outputs.

Case-study origins for Figure 4 are chosen by a fixed rule, not by eye: among
the focus origins, the most and the least divergent (mean percentile of the
rarefied Jensen-Shannon divergence across every available window and counting
method; rarefied so that origins with more papers are not mechanically ranked
as less divergent). Figure titles are taken from ``outputs/figure_titles.json`` when
present, which is written only after results are known; otherwise neutral
descriptive titles are used.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..analysis import run
from ..config import PATHS, load_config, window as get_window
from . import figures as F


def _table(name: str) -> pd.DataFrame | None:
    p = PATHS.tables / name
    return pd.read_csv(p, keep_default_na=False, na_values=[""]) if p.exists() else None


def choose_case_studies(focus: list[str]) -> list[str]:
    tabs = [t for t in [_table(f"alignment_{w}{s}.csv") for w in ("earlier", "primary", "later") for s in ("", "_frac")] if t is not None]
    pct = []
    for t in tabs:
        col = "jsd_rarefied" if "jsd_rarefied" in t else "jsd_raw"
        t = t.dropna(subset=[col])
        pct.append(t.set_index("origin")[col].rank(pct=True))
    if not pct:
        return focus[:2]
    m = pd.concat(pct, axis=1).mean(axis=1).reindex(focus).dropna()
    if len(m) < 2:
        return m.index.tolist()
    return [m.idxmax(), m.idxmin()]


def titles() -> dict:
    p = PATHS.outputs / "figure_titles.json"
    return json.loads(p.read_text()) if p.exists() else {}


def make_figures(windows: list[str] | None = None) -> list[Path]:
    cfg = load_config()
    focus = cfg["countries"]["focus_origins"]
    windows = windows or [w for w in ("earlier", "primary", "later") if (PATHS.tables / f"alignment_{w}.csv").exists()]
    T = titles()
    out: list[Path] = []
    wd = run.load_window("primary")
    label = get_window("primary")["label"]
    L = run.layers(wd, "full")
    coords = pd.read_csv(PATHS.processed / "country_coords.csv")
    out += F.figure1_three_networks(L, coords, focus, PATHS.figures, label, **({"title": T["fig1"]} if "fig1" in T else {}))
    al = _table("alignment_primary.csv")
    origins = [o for o in focus if o in set(al["origin"])]
    comp = _table("comparators_primary.csv")
    if comp is not None:
        origins += [c for c in comp["comparator"].dropna() if c in set(al["origin"]) and c not in origins]
    mat = F.divergence_matrix(L["migration"], L["collaboration"], origins)
    jcol = "jsd_rarefied" if "jsd_rarefied" in al else "jsd_raw"
    out += F.figure2_divergence(mat, PATHS.figures, label, al.set_index("origin")[jcol],
                                **({"title": T["fig2"]} if "fig2" in T else {}))
    res = _table("residuals_primary.csv")
    out += F.figure3_expected_observed(res, PATHS.figures, label, focus, **({"title": T["fig3"]} if "fig3" in T else {}))
    cases = choose_case_studies(focus)
    out += F.figure4_case(L, res, cases, PATHS.figures, label, **({"title": T["fig4"]} if "fig4" in T else {}))
    align = {w: _table(f"alignment_{w}.csv") for w in windows}
    grav = {w: _table(f"gravity_{w}.csv") for w in windows}
    out += F.figure5_temporal({k: v for k, v in align.items() if v is not None},
                              {k: v for k, v in grav.items() if v is not None}, focus, PATHS.figures,
                              **({"title": T["fig5"]} if "fig5" in T else {}))
    summ = json.loads((PATHS.models / "gravity_primary.json").read_text())
    out += F.figure6_coefficients(grav["primary"], summ.get("cv", []), PATHS.figures, label,
                                  **({"title": T["fig6"]} if "fig6" in T else {}))
    out += interactive(res, al)
    (PATHS.outputs / "case_study_selection.json").write_text(json.dumps({"rule": __doc__.split("\n\n")[1], "selected": cases}, indent=2))
    return out


def interactive(res: pd.DataFrame, al: pd.DataFrame) -> list[Path]:
    import plotly.express as px
    from ..cleaning import countries as C

    paths = []
    d = res.copy()
    d["pair"] = d["a"].map(C.name) + " – " + d["b"].map(C.name)
    d["x"] = d["expected"] + 1
    d["y"] = d["observed"] + 1
    fig = px.scatter(d, x="x", y="y", color="category", hover_name="pair", log_x=True, log_y=True,
                     hover_data={"observed": True, "expected": ":.1f", "log_ratio": ":.2f", "q_bh": ":.3g",
                                 "mig_ab": True, "mig_ba": True, "mob_ab": True, "mob_ba": True, "x": False, "y": False},
                     color_discrete_map={"stronger_than_expected": "#2a78d6", "weaker_than_expected": "#e34948",
                                         "as_expected": "#c3c2b7", "insufficient_information": "#e1e0d9", "missing_link": "#eb6834"},
                     labels={"x": "Expected co-authored articles (model M2) + 1", "y": "Observed co-authored articles + 1"},
                     title="Observed vs expected co-authorship, all country pairs (primary window)")
    fig.update_layout(template="simple_white", font_family="system-ui, sans-serif")
    p = PATHS.figures / "interactive_expected_vs_observed.html"
    fig.write_html(p, include_plotlyjs="cdn")
    paths.append(p)
    a = al.copy()
    a["country"] = a["origin"].map(C.name)
    jcol = "jsd_rarefied" if "jsd_rarefied" in a else "jsd_raw"
    fig2 = px.scatter(a, x="log_output", y=jcol, color="ssa", hover_name="country",
                      hover_data={"spearman_raw": ":.2f", "spearman_resid": ":.2f", "top10_overlap": ":.1f",
                                  "emigrants": ":,.0f", "intl_collab": ":,.0f"},
                      labels={"log_output": "ln research output (articles, capacity window)",
                              jcol: "Jensen–Shannon divergence, migrants vs co-authorship (rarefied to 50 incidences)",
                              "ssa": "Sub-Saharan Africa"},
                      title="Per-origin divergence between migrant destinations and co-authorship partners")
    fig2.update_layout(template="simple_white", font_family="system-ui, sans-serif")
    p2 = PATHS.figures / "interactive_alignment_by_origin.html"
    fig2.write_html(p2, include_plotlyjs="cdn")
    paths.append(p2)
    return paths
