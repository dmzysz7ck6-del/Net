"""Project paths and configuration loading.

All modules obtain paths and analytical parameters from here so the pipeline
has one source of truth (``config/pipeline.yaml``).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "pipeline.yaml"


class Paths:
    """All project paths, derived from one root (tests point it at a tmp dir)."""

    def __init__(self, root: Path = ROOT):
        self.root = Path(root)
        self.raw = self.root / "data" / "raw"
        self.interim = self.root / "data" / "interim"
        self.processed = self.root / "data" / "processed"
        self.research = self.root / "research"
        self.figures = self.root / "figures"
        self.outputs = self.root / "outputs"
        self.tables = self.outputs / "tables"
        self.models = self.outputs / "models"
        self.manifest = self.raw / "MANIFEST.jsonl"
        self.request_log = self.raw / "openalex" / "requests.jsonl"

    def ensure(self) -> "Paths":
        for p in (self.raw, self.interim, self.processed, self.figures, self.tables, self.models):
            p.mkdir(parents=True, exist_ok=True)
        return self

    def set_root(self, root: Path) -> None:
        self.__init__(root)


PATHS = Paths()


@lru_cache(maxsize=1)
def load_config(path: str | os.PathLike | None = None) -> dict[str, Any]:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def window(name: str) -> dict[str, Any]:
    cfg = load_config()
    try:
        return cfg["windows"][name]
    except KeyError as exc:  # pragma: no cover - configuration error
        raise KeyError(f"unknown window {name!r}; known: {list(cfg['windows'])}") from exc


def seed() -> int:
    return int(load_config()["project"]["seed"])


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader (no dependency): KEY=VALUE lines, # comments.

    Existing environment variables are never overwritten.
    """
    path = path or (ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
