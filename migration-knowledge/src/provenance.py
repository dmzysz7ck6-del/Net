"""Provenance records for every acquired or derived file.

Each acquisition appends one JSON line to ``data/raw/MANIFEST.jsonl`` with the
source URL, timestamp, SHA-256, size, licence and any query parameters, so a
reader can verify exactly what the analysis was run on.
"""
from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PATHS


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record(path: Path, *, source: str, url: str | None = None, license: str | None = None,
           params: dict[str, Any] | None = None, rows: int | None = None,
           note: str | None = None, manifest: Path | None = None) -> dict[str, Any]:
    """Append a provenance entry for ``path`` and return it."""
    manifest = manifest or PATHS.manifest
    manifest.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "file": str(Path(path).resolve().relative_to(PATHS.root)) if Path(path).resolve().is_relative_to(PATHS.root) else str(path),
        "source": source,
        "url": url,
        "license": license,
        "retrieved_utc": utcnow(),
        "sha256": sha256(Path(path)) if Path(path).exists() else None,
        "bytes": Path(path).stat().st_size if Path(path).exists() else None,
        "rows": rows,
        "params": params or {},
        "note": note,
        "python": platform.python_version(),
    }
    with open(manifest, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def latest(source: str, manifest: Path | None = None) -> dict[str, Any] | None:
    manifest = manifest or PATHS.manifest
    if not manifest.exists():
        return None
    found = None
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("source") == source:
            found = entry
    return found
