"""Command-line entry point: ``python -m src.pipeline <stage>``.

Stages
------
check-access   test reachability of every data host (writes outputs/access_check.json)
acquire        download all sources (resumable); ``--pilot`` = four-origin pilot only
clean          build the processed data contract
analyze        run all pre-registered analyses for every design window
figures        regenerate all figures from outputs
quality        write research/data_quality_report.md
all            everything above in order (stops at the first failure)
"""
from __future__ import annotations

import argparse
import json
import sys

from .config import PATHS, load_config, load_dotenv

HOSTS = {
    "OpenAlex API": "https://api.openalex.org/works?per_page=1",
    "UN DESA": "https://www.un.org/development/desa/pd/content/international-migrant-stock",
    "Zenodo": "https://zenodo.org/api/records/11145735",
    "World Bank API": "https://api.worldbank.org/v2/country?format=json&per_page=1",
    "CEPII": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=6",
    "Crossref": "https://api.crossref.org/works?rows=1",
}


def check_access() -> dict:
    from .http import check_hosts
    res = check_hosts(HOSTS.values())
    out = {name: res[url] for name, url in HOSTS.items()}
    PATHS.ensure()
    (PATHS.outputs / "access_check.json").write_text(json.dumps(out, indent=2))
    for k, v in out.items():
        print(f"{k:16s} {v}")
    return out


def acquire(pilot: bool = False) -> None:
    from .acquisition import covariates, openalex, scholarly, undesa
    from .cleaning import countries as C

    cfg = load_config()
    undesa.acquire()
    scholarly.acquire()
    covariates.acquire_wdi()
    covariates.acquire_cepii()
    cw = C.crosswalk()
    if pilot:
        codes = [C.iso3_to_iso2(c) for c in cfg["countries"]["pilot_origins"]]
        openalex.extract_window("primary", codes)
        for c in codes:
            openalex.extract_works(c, tuple(cfg["windows"]["primary"]["collab_years"]))
        return
    codes = [c for c in cw["iso2"] if c not in ("XK",)]
    seen_years = set()
    for name, w in cfg["windows"].items():
        cy = tuple(w["collab_years"])
        if cy not in seen_years:
            openalex.extract_window(name, codes)
            seen_years.add(cy)
        openalex.extract_outputs(tuple(w["capacity_years"]), codes)
    oa = openalex.OpenAlex()
    oa.coverage((2005, 2024)).to_csv(PATHS.raw / "openalex" / "coverage_by_year.csv", index=False)
    for c in cfg["countries"]["focus_origins"]:
        openalex.extract_works(C.iso3_to_iso2(c), tuple(cfg["windows"]["primary"]["collab_years"]))


def clean() -> None:
    from .cleaning.build import build_all
    build_all()


def analyze(windows: list[str] | None = None) -> None:
    from .analysis import run
    windows = windows or ["primary", "earlier", "later", "contemporaneous"]
    for w in windows:
        print(f"== window {w}")
        run.run_window(w, robustness=(w == "primary"))


def figures() -> None:
    from .visualization.make import make_figures
    for p in make_figures():
        print(p.relative_to(PATHS.root))


def quality() -> None:
    from .reporting.quality import write_report
    print(write_report())


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    ap = argparse.ArgumentParser(prog="python -m src.pipeline", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["check-access", "acquire", "clean", "analyze", "figures", "quality", "all"])
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--window", action="append")
    a = ap.parse_args(argv)
    if a.stage == "check-access":
        res = check_access()
        return 0 if all(v == "ok" for v in res.values()) else 2
    if a.stage in ("acquire", "all"):
        res = check_access()
        blocked = [k for k, v in res.items() if v != "ok" and k != "Crossref"]
        if blocked:
            print(f"cannot acquire: blocked hosts {blocked}. See README 'Network access'.", file=sys.stderr)
            return 2
        acquire(pilot=a.pilot)
        if a.stage == "acquire":
            return 0
    if a.stage in ("clean", "all"):
        clean()
    if a.stage in ("analyze", "all"):
        analyze(a.window)
    if a.stage in ("quality", "all"):
        quality()
    if a.stage in ("figures", "all"):
        figures()
    return 0


if __name__ == "__main__":
    sys.exit(main())
