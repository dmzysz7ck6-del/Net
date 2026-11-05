"""World Bank WDI (API v2) and CEPII GeoDist acquisition."""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from ..config import PATHS, load_config
from ..http import CachedClient
from .. import provenance


def acquire_wdi(years: tuple[int, int] = (2005, 2024)) -> pd.DataFrame:
    cfg = load_config()["sources"]["wdi"]
    client = CachedClient(PATHS.raw / "wdi" / "cache", requests_per_second=2)
    frames = []
    for name, code in cfg["indicators"].items():
        url = f"{cfg['base_url']}/country/all/indicator/{code}"
        params = {"format": "json", "date": f"{years[0]}:{years[1]}", "per_page": 20000}
        data = client.get_json(url, params)
        meta, rows = data[0], data[1] or []
        if int(meta.get("pages", 1)) > 1:  # pragma: no cover - per_page is large enough today
            raise RuntimeError(f"WDI {code}: unexpected pagination {meta}")
        frames.append(pd.DataFrame([{"wdi_code": r.get("countryiso3code") or r["country"]["id"],
                                     "country_name": r["country"]["value"], "year": int(r["date"]),
                                     "indicator": name, "value": r["value"]} for r in rows]))
    df = pd.concat(frames, ignore_index=True)
    meta = client.get_json(f"{cfg['base_url']}/country", {"format": "json", "per_page": 1000})
    countries = pd.DataFrame([{"wdi_code": c["id"], "iso2_wb": c.get("iso2Code"), "region": c["region"]["value"],
                               "region_id": c["region"]["id"], "income": c["incomeLevel"]["value"],
                               "income_id": c["incomeLevel"]["id"]} for c in meta[1]])
    out = PATHS.raw / "wdi" / "wdi_long.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    countries.to_csv(PATHS.raw / "wdi" / "wdi_countries.csv", index=False)
    provenance.record(out, source="wdi", url=cfg["base_url"], license=cfg["license"], rows=len(df),
                      params={"indicators": cfg["indicators"], "years": list(years)})
    provenance.record(PATHS.raw / "wdi" / "wdi_countries.csv", source="wdi_countries", url=f"{cfg['base_url']}/country",
                      license=cfg["license"], rows=len(countries))
    return df


def acquire_cepii() -> dict[str, Path]:
    cfg = load_config()["sources"]["cepii_geodist"]
    client = CachedClient(PATHS.raw / "cepii" / "cache", requests_per_second=1)
    out = {}
    for key in ("dist_url", "geo_url"):
        url = cfg[key]
        dest = PATHS.raw / "cepii" / Path(url).name
        existed = dest.exists()
        client.download(url, dest)
        if not existed:
            provenance.record(dest, source=f"cepii_{key[:-4]}", url=url, license=cfg["license"])
        if dest.suffix == ".zip":
            with zipfile.ZipFile(dest) as zf:
                for member in zf.namelist():
                    if member.lower().endswith((".dta", ".xls", ".xlsx", ".csv")):
                        target = dest.parent / Path(member).name
                        if not target.exists():
                            target.write_bytes(zf.read(member))
                        out[Path(member).name] = target
        else:
            out[dest.name] = dest
    return out
