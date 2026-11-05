"""Download the UN DESA International Migrant Stock 2024 destination-and-origin
workbook (original file, unmodified) and record its provenance."""
from __future__ import annotations

from pathlib import Path

from ..config import PATHS, load_config
from ..http import CachedClient
from .. import provenance


def acquire(refresh: bool = False) -> Path:
    cfg = load_config()["sources"]["undesa_ims"]
    dest = PATHS.raw / "undesa" / Path(cfg["url"]).name
    client = CachedClient(PATHS.raw / "undesa" / "cache", requests_per_second=1)
    existed = dest.exists()
    client.download(cfg["url"], dest, refresh=refresh)
    if refresh or not existed:
        provenance.record(dest, source="undesa_ims_2024", url=cfg["url"], license=cfg["license"],
                          note=f"{cfg['revision']}; landing page {cfg['landing']}")
    return dest
