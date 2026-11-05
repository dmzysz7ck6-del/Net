"""`make verify`: fail if any rendered document has untraceable numbers."""
from __future__ import annotations

import sys

from ..config import PATHS
from .claims import verify

DOCS = [PATHS.outputs / "research_report.md", PATHS.outputs / "findings.md", PATHS.root / "blog" / "essay.md"]


def main() -> int:
    problems = verify(DOCS)
    for p in problems:
        print(p)
    if not any(d.exists() for d in DOCS):
        print("no rendered documents yet (analysis not run)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
