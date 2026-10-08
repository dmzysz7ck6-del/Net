"""Command line: `ossnet <repository path or URL>`."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from . import __version__
from .health import analyze
from .history import DEFAULT_IGNORE, GitError, clone, load_history
from .report import render_html, render_text


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ossnet",
        description="Network-science health check for an open-source community, from its git history.",
    )
    p.add_argument("repo", help="path to a git repository, or a URL to clone")
    p.add_argument("-o", "--out", type=Path, help="output directory (default: ossnet-reports/<repo>)")
    p.add_argument("--period", choices=("month", "quarter", "year"), default="quarter",
                   help="timeline granularity (default: quarter)")
    p.add_argument("--since", help="only read commits after this date, e.g. 2018-01-01")
    p.add_argument("--horizon-days", type=int, default=365,
                   help="a newcomer 'stays' if they commit between this many days and twice that "
                        "after joining (default: 365)")
    p.add_argument("--early-days", type=int, default=90,
                   help="length of a newcomer's early window (default: 90)")
    p.add_argument("--peer-days", type=int, default=30,
                   help="early peers include people who changed the same files this long before "
                        "the newcomer joined (default: 30)")
    p.add_argument("--max-files", type=int, default=50,
                   help="commits touching more files are treated as bulk changes (default: 50)")
    p.add_argument("--max-editors", type=int, default=50,
                   help="files with more editors add no network ties (default: 50)")
    p.add_argument("--ignore", action="append", default=[], metavar="PATTERN",
                   help="extra file pattern to ignore, e.g. 'docs/*' (repeatable)")
    p.add_argument("--keep-bots", action="store_true", help="count bot accounts as people")
    p.add_argument("--no-renames", action="store_true",
                   help="skip rename detection (faster on clones without file contents)")
    p.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "ossnet",
                   help="where URLs are cloned (default: ~/.cache/ossnet)")
    p.add_argument("--refresh", action="store_true", help="fetch new commits for a cached clone")
    p.add_argument("--json", action="store_true", help="print the full analysis as JSON instead of a summary")
    p.add_argument("--version", action="version", version=f"ossnet {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo: str | Path = args.repo
        if re.match(r"^(https?|ssh|git)://|^[\w.-]+@[\w.-]+:", args.repo):
            repo = clone(args.repo, args.cache, refresh=args.refresh)
        history = load_history(
            repo,
            renames=not args.no_renames,
            since=args.since,
            keep_bots=args.keep_bots,
            ignore=DEFAULT_IGNORE + tuple(args.ignore),
            max_files=args.max_files,
        )
        result = analyze(
            history,
            unit=args.period,
            horizon_days=args.horizon_days,
            early_days=args.early_days,
            peer_lookback_days=args.peer_days,
            max_editors=args.max_editors,
        )
    except (GitError, ValueError) as e:
        print(f"ossnet: {e}", file=sys.stderr)
        return 1

    out = args.out or Path("ossnet-reports") / re.sub(r"[^\w.-]+", "_", result["repo"])
    write_outputs(result, out)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_text(result))
        print(f"\nReport: {out / 'report.html'}")
    return 0


def write_outputs(result: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(result, indent=2))
    (out / "report.html").write_text(render_html(result))
    _write_csv(out / "timeline.csv", result["timeline"])
    _write_csv(out / "newcomers.csv", result["newcomers"])
    _write_csv(out / "contributors.csv", [
        {**c, "aliases": "; ".join(c["aliases"])} for c in result["contributors"]
    ])


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        if not rows:
            return
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())
