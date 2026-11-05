"""Traceable numbers for the written outputs.

Prose documents are written as templates (``research/templates/*.md``) with
tokens such as ``{{h1.median_rho_resid:.2f}}``. ``collect()`` builds a flat
registry of every number the analysis produced, each with the file it came
from; ``render()`` substitutes tokens and writes a sidecar listing every
inserted value and its source. ``verify()`` fails if a rendered document
contains an unresolved token or a claim whose source file no longer exists,
so every quantitative statement is traceable to a generated output.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..config import PATHS

TOKEN = re.compile(r"\{\{\s*([A-Za-z0-9_.\-\[\]]+)\s*(?::([^}]+))?\}\}")


def _flatten(prefix: str, obj: Any, src: str, out: dict) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten(f"{prefix}.{k}" if prefix else str(k), v, src, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _flatten(f"{prefix}[{i}]", v, src, out)
    else:
        out[prefix] = {"value": obj, "source": src}


def collect() -> dict:
    reg: dict = {}
    for p in sorted(PATHS.models.glob("*.json")):
        _flatten(p.stem, json.loads(p.read_text()), str(p.relative_to(PATHS.root)), reg)
    extra = PATHS.outputs / "derived_claims.json"
    if extra.exists():
        for k, v in json.loads(extra.read_text()).items():
            reg[k] = v
    (PATHS.outputs / "claims_registry.json").write_text(json.dumps(reg, indent=1, default=str))
    return reg


def render(template: Path, target: Path, registry: dict | None = None) -> Path:
    registry = registry or collect()
    used = []

    def sub(m: re.Match) -> str:
        key, fmt = m.group(1), m.group(2)
        if key not in registry:
            raise KeyError(f"{template.name}: unknown claim {key!r}")
        v = registry[key]["value"]
        used.append({"key": key, "value": v, "source": registry[key]["source"]})
        if fmt and isinstance(v, (int, float)):
            if fmt.endswith("%"):
                return format(v, fmt)
            return format(v, fmt)
        return str(v)

    text = TOKEN.sub(sub, template.read_text(encoding="utf-8"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    target.with_suffix(".claims.json").write_text(json.dumps(used, indent=1, default=str))
    return target


def verify(docs: list[Path]) -> list[str]:
    problems = []
    for d in docs:
        if not d.exists():
            continue
        text = d.read_text(encoding="utf-8")
        if TOKEN.search(text):
            problems.append(f"{d}: unresolved claim tokens")
        side = d.with_suffix(".claims.json")
        if side.exists():
            for c in json.loads(side.read_text()):
                if not (PATHS.root / c["source"]).exists():
                    problems.append(f"{d}: claim {c['key']} cites missing source {c['source']}")
    return problems
