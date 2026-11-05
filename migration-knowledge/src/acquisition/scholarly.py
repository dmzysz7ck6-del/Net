"""Download the released scholarly-migration data (Akbaritabar, Theile &
Zagheni 2024, Scientific Data) from Zenodo, verifying each file's checksum
against the record metadata and recording licence and version."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..config import PATHS, load_config
from ..http import CachedClient
from .. import provenance


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def acquire(max_file_mb: float = 2000) -> list[Path]:
    cfg = load_config()["sources"]["scholarly_migration"]
    client = CachedClient(PATHS.raw / "scholarly" / "cache", requests_per_second=1)
    record = client.get_json(cfg["zenodo_api"])
    out_dir = PATHS.raw / "scholarly" / f"zenodo_{record.get('id', cfg['zenodo_record'])}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "record.json").write_text(json.dumps(record, indent=2))
    meta = record.get("metadata", {})
    lic = (meta.get("license") or {}).get("id") if isinstance(meta.get("license"), dict) else meta.get("license")
    paths = []
    for f in record.get("files", []):
        name = f.get("key") or f.get("filename")
        url = (f.get("links") or {}).get("self") or (f.get("links") or {}).get("content")
        size_mb = (f.get("size") or 0) / 1e6
        if size_mb > max_file_mb:
            provenance.record(out_dir / "record.json", source="scholarly_skipped_file", url=url,
                              note=f"skipped {name} ({size_mb:.0f} MB > {max_file_mb} MB limit)")
            continue
        dest = out_dir / name
        existed = dest.exists()
        client.download(url, dest)
        checksum = f.get("checksum", "")
        if checksum.startswith("md5:") and _md5(dest) != checksum[4:]:
            dest.unlink()
            raise RuntimeError(f"checksum mismatch for {name}")
        if not existed:
            provenance.record(dest, source="scholarly_migration_zenodo", url=url, license=lic,
                              params={"record": record.get("id"), "version": meta.get("version"),
                                      "doi": record.get("doi") or meta.get("doi"), "checksum": checksum})
        paths.append(dest)
    return paths
