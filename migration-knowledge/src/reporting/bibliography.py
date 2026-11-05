"""Render research/bibliography.md from research/references.json."""
from __future__ import annotations

import json

from ..config import PATHS

LEVELS = {"V3": "verified against Crossref", "V2": "independently re-verified", "V1": "single-pass search match",
          "U": "unverified / no DOI", "X": "Crossref MISMATCH"}


def render() -> str:
    path = PATHS.research / "references_verified.json"
    refs = json.loads((path if path.exists() else PATHS.research / "references.json").read_text())
    lines = ["# Annotated bibliography", "",
             "Generated from `research/references.json` by `python -m src.reporting.bibliography`. "
             "Labels: " + "; ".join(f"**{k}** = {v}" for k, v in LEVELS.items()) + ". "
             "Findings are abstract-level summaries unless stated otherwise.", ""]
    for r in refs:
        link = f"https://doi.org/{r['doi']}" if r.get("doi") else r.get("url", "")
        lines += [f"### {r['authors']} ({r['year']}). {r['title']}",
                  f"*{r['venue']}*. {('DOI: [' + r['doi'] + '](' + link + ')') if r.get('doi') else ('Link: ' + link)} · "
                  f"**{r['level']}** ({LEVELS.get(r['level'], '')})", "",
                  f"- **Question:** {r['research_question']}",
                  f"- **Data:** {r['data']}",
                  f"- **Methods:** {r['methods']}",
                  f"- **Findings:** {r['findings']}",
                  f"- **Relevance here:** {r['relevance_to_project']}", ""]
    out = PATHS.research / "bibliography.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    print(render())
