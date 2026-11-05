"""`make verify-refs`: check every DOI in research/references.json against
Crossref (title similarity >= 0.85, publication year within 1, first-author
family name present). Writes research/references_verified.json with level V3
(verified) or X (mismatch); entries without DOI keep their label."""
from __future__ import annotations

import difflib
import json
import re
import sys

from ..config import PATHS
from ..http import AccessDenied, CachedClient


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower())


def main() -> int:
    refs = json.loads((PATHS.research / "references.json").read_text())
    client = CachedClient(PATHS.raw / "crossref" / "cache", requests_per_second=2)
    out, bad = [], 0
    for r in refs:
        r = dict(r)
        if r.get("doi"):
            try:
                msg = client.get_json(f"https://api.crossref.org/works/{r['doi']}")["message"]
            except AccessDenied:
                print("api.crossref.org is blocked by the network policy; nothing verified")
                return 2
            except Exception as exc:  # 404 etc.
                r.update(level="X", crossref_note=f"lookup failed: {exc!r}")
                bad += 1
                out.append(r)
                continue
            title = (msg.get("title") or [""])[0]
            year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
            fams = [norm(a.get("family", "")) for a in msg.get("author", [])]
            sim = difflib.SequenceMatcher(None, norm(title), norm(r["title"])).ratio()
            first = norm(r["authors"].split(";")[0].split(",")[0]).split()
            ok = sim >= 0.85 and (year is None or abs(int(year) - int(r["year"])) <= 1) and (not fams or any(f in first for f in fams[:1]) or any(f and f in norm(r["authors"]) for f in fams[:2]))
            r.update(level="V3" if ok else "X", crossref_title=title, crossref_year=year, title_similarity=round(sim, 3))
            bad += not ok
        out.append(r)
    (PATHS.research / "references_verified.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"checked {sum(1 for r in refs if r.get('doi'))} DOIs; mismatches: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
