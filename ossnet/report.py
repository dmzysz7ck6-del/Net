"""Render an analysis as a terminal summary or a self-contained HTML report."""

from __future__ import annotations

import html
import json
from pathlib import Path

from . import __version__

_ASSETS = Path(__file__).parent


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.0%}"


def _rate(r: dict) -> str:
    if not r["newcomers"]:
        return "n/a"
    return f"{pct(r['stay_rate'])} ({r['stayed']} of {r['newcomers']})"


def _people(names: list[str]) -> str:
    if len(names) <= 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + ", and " + names[-1]


def _plural(n: int, word: str, plural: str | None = None) -> str:
    return f"{n:,} {word if n == 1 else plural or word + 's'}"


def _network_size(n: dict) -> str:
    return (f"{_plural(n['people'], 'person', 'people')}, {_plural(n['ties'], 'tie')}, "
            f"{_plural(n['communities'], 'community', 'communities')}")


def stay_window(days: int, short: bool = False) -> str:
    """When a newcomer must commit again to count as staying."""
    span = "12–24 months" if days == 365 else f"{days:,}–{2 * days:,} days"
    return f"{span} later" if short else f"{span} after their first commit"


def findings(r: dict) -> list[str]:
    """The handful of plain-language takeaways at the top of the report."""
    h, cur = r["history"], r["current"]
    k, ret, ties = cur["knowledge"], r["retention"]["overall"], r["newcomer_ties"]
    out = []
    if h["days_since_last_commit"] > 180:
        out.append(f"No commits in the {h['days_since_last_commit']:,} days before this report; "
                   "everything below describes the project as it was.")
    people = k["truck_factor_people"]
    if people:
        line = (f"Truck factor {k['truck_factor']}: if {_people([p['person'] for p in people])} left, "
                f"more than half of the {k['files']:,} tracked files would have no remaining main author.")
        gone = [p["person"] for p in people if not p["active"]]
        if gone:
            line += f" {_people(gone)} {'has' if len(gone) == 1 else 'have'} not committed in over a year."
        out.append(line)
    if k["authors_gone_share"]:
        out.append(f"For {pct(k['authors_gone_share'])} of files, every main author has gone a year without committing.")
    top = cur["top_contributor"]
    if top:
        out.append(f"{top['person']} made {pct(top['share'])} of the last 12 months' commits; "
                   f"{_plural(len(cur['core_80']), 'person', 'people')} made 80% of them.")
    if cur["assisted_share"]:
        out.append(f"{pct(cur['assisted_share'])} of the last 12 months' commits were signed by an AI assistant.")
    if ret["observed"]:
        out.append(f"{pct(ret['stay_rate'])} of newcomers committed again "
                   f"{stay_window(r['retention']['horizon_days'])}; "
                   f"{pct(ret['one_time_share'])} never made a second commit.")
    one, more = ties["by_early_commits"]["1"]["all"], ties["by_early_commits"]["2+"]["all"]
    if one["newcomers"] >= 20 and more["newcomers"] >= 20:
        out.append(f"Newcomers with two or more commits in their first {r['settings']['early_days']} days "
                   f"stayed at {pct(more['stay_rate'])}, against {pct(one['stay_rate'])} for one-commit newcomers.")
    tied, apart = ties["tied"], ties["not_tied"]
    if tied["newcomers"] >= 20 and apart["newcomers"] >= 20:
        overlap = tied["ci95"][0] <= apart["ci95"][1] and apart["ci95"][0] <= tied["ci95"][1]
        out.append(f"Newcomers whose early work overlapped with the core team's stayed at {pct(tied['stay_rate'])}, "
                   f"against {pct(apart['stay_rate'])} for those whose didn't"
                   + ("; the confidence intervals overlap, so this is no clear difference." if overlap else "."))
    return out


def render_text(r: dict) -> str:
    h, cur = r["history"], r["current"]
    k, n, ret, ties = cur["knowledge"], cur["network"], r["retention"]["overall"], r["newcomer_ties"]
    top = cur["top_contributor"]
    tf_people = ", ".join(p["person"] + ("" if p["active"] else " (inactive)") for p in k["truck_factor_people"])
    lines = [
        f"{r['repo']}: {h['commits']:,} commits by {h['people']:,} people, {h['first_commit']} to {h['last_commit']}",
        "",
        f"Last 12 months ({cur['window']['start']} to {cur['window']['end']})",
        f"  Activity       {cur['commits']:,} commits from {_plural(cur['contributors'], 'person', 'people')}, "
        f"{cur['newcomers']} of them new",
        f"  Concentration  {_plural(len(cur['core_80']), 'person', 'people')} made 80% of commits"
        + (f"; {top['person']} made {pct(top['share'])}" if top else ""),
        f"  Truck factor   {k['truck_factor']}" + (f": {tf_people}" if tf_people else ""),
        f"  Know-how       {pct(k['single_author_share'])} of files have one main author; "
        f"for {pct(k['authors_gone_share'])}, every main author has gone a year without committing",
    ]
    if n["ties"]:
        lines.append(
            f"  Network        {_network_size(n)} (modularity {n['modularity']:.2f})"
            + (f", core of {n['core_size']} (fit {n['core_fit']:.2f})" if n["core_size"] else "")
        )
    if cur["brokers"]:
        lines.append(f"  Brokers        {', '.join(b['person'] for b in cur['brokers'][:3])}")
    if cur["assisted_share"]:
        lines.append(f"  AI-assisted    {pct(cur['assisted_share'])} of commits")
    lines += [
        "",
        f"Newcomers who stayed (committed again {stay_window(r['retention']['horizon_days'])})",
        f"  Overall        {pct(ret['stay_rate'])} ({ret['stayed']} of {ret['observed']}); "
        f"{pct(ret['one_time_share'])} made a single commit",
        f"  Early work     1 commit: {_rate(ties['by_early_commits']['1']['all'])}; "
        f"2+ commits: {_rate(ties['by_early_commits']['2+']['all'])}",
        f"  Early core tie with: {_rate(ties['tied'])}; without: {_rate(ties['not_tied'])}",
    ]
    return "\n".join(lines)


def _payload(r: dict) -> dict:
    """The subset of the analysis the report's charts draw from."""
    ties = r["newcomer_ties"]
    early = r["settings"]["early_days"]
    rows = [
        ("All newcomers", ties["all"]),
        ("Overlapped with core", ties["tied"]),
        ("Did not overlap", ties["not_tied"]),
        (f"1 commit in first {early} days", ties["by_early_commits"]["1"]["all"]),
        ("  …overlapped with core", ties["by_early_commits"]["1"]["tied"]),
        ("  …did not overlap", ties["by_early_commits"]["1"]["not_tied"]),
        (f"2+ commits in first {early} days", ties["by_early_commits"]["2+"]["all"]),
        ("  …overlapped with core", ties["by_early_commits"]["2+"]["tied"]),
        ("  …did not overlap", ties["by_early_commits"]["2+"]["not_tied"]),
    ]
    peers = [(f"{label} early peer{'' if label == '1' else 's'}", v) for label, v in ties["by_early_peers"].items()]
    snap = r["snapshot"]
    return {
        "timeline": [
            {
                "period": t["period"],
                "commits": t["commits"],
                "contributors": t["contributors"],
                "newcomers": t["newcomers"],
                "truckFactor": t["truck_factor"],
                "core80": t["year_core_80"],
                "yearContributors": t["year_contributors"],
                "inProgress": t["in_progress"],
            }
            for t in r["timeline"]
        ],
        "cohorts": [
            {"year": c["year"], "observed": c["observed"], "stayed": c["stayed"], "rate": c["stay_rate"],
             "lo": c["stay_rate_ci95"][0], "hi": c["stay_rate_ci95"][1]}
            for c in r["retention"]["cohorts"] if c["observed"]
        ],
        "ties": [
            {"label": label, "rate": v["stay_rate"], "lo": v["ci95"][0], "hi": v["ci95"][1],
             "n": v["newcomers"], "stayed": v["stayed"], "indent": label.startswith("  ")}
            for label, v in rows if v["newcomers"]
        ],
        "peers": [
            {"label": label, "rate": v["stay_rate"], "lo": v["ci95"][0], "hi": v["ci95"][1],
             "n": v["newcomers"], "stayed": v["stayed"]}
            for label, v in peers if v["newcomers"]
        ],
        "network": {
            "shown": snap["shown"],
            "total": snap["total"],
            "nodes": snap["nodes"],
            "edges": snap["edges"],
        },
    }


def _table(head: list[str], rows: list[list], numeric: set[int] = frozenset()) -> str:
    th = "".join(f'<th{" class=num" if i in numeric else ""}>{html.escape(h)}</th>' for i, h in enumerate(head))
    body = "".join(
        "<tr>" + "".join(
            f'<td{" class=num" if i in numeric else ""}>{html.escape(str(v))}</td>' for i, v in enumerate(row)
        ) + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def _tile(label: str, value: str, note: str, spark: str | None = None) -> str:
    chart = f'<div class="spark" data-spark="{spark}" aria-hidden="true"></div>' if spark else ""
    return (f'<div class="tile"><div class="tile-label">{html.escape(label)}</div>'
            f'<div class="tile-value">{html.escape(value)}</div>{chart}'
            f'<div class="tile-note">{html.escape(note)}</div></div>')


def render_html(r: dict) -> str:
    esc = html.escape
    h, cur, s = r["history"], r["current"], r["settings"]
    k, n, ret = cur["knowledge"], cur["network"], r["retention"]
    top = cur["top_contributor"]
    payload = _payload(r)
    data = json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")
    period = s["period"]

    tiles = "".join([
        _tile("Truck factor", str(k["truck_factor"]),
              f"people whose departure would leave most files without a main author", "truckFactor"),
        _tile("People doing 80% of the work", str(len(cur["core_80"])),
              f"top: {top['person']}, {pct(top['share'])} of commits" if top else "no commits in the last year",
              "core80"),
        _tile("Contributors, last 12 months", f"{cur['contributors']:,}",
              f"{cur['newcomers']:,} of them new", "yearContributors"),
        _tile("Newcomers who stayed", pct(ret["overall"]["stay_rate"]),
              f"committed again {stay_window(ret['horizon_days'], short=True)}; "
              f"{pct(ret['overall']['one_time_share'])} made a single commit"),
    ])

    tf_rows = [
        [p["person"], f"{p['files']:,}", pct(p["share"]), p["last_commit"], "active" if p["active"] else "inactive"]
        for p in k["truck_factor_people"]
    ]
    contributors = [c for c in r["contributors"] if c["active_last_year"]]
    contributors.sort(key=lambda c: (-c["commits_last_year"], c["person"]))
    contributor_rows = [
        [c["person"], f"{c['commits_last_year']:,}", f"{c['commits']:,}", c["first"], "yes" if c["core_80"] else ""]
        for c in contributors[:15]
    ]
    groups = cur["communities"]
    community_rows = [
        [f"Community {i + 1}" + ("" if i < 3 else " (gray)"), len(g), ", ".join(g[:8]) + (" …" if len(g) > 8 else "")]
        for i, g in enumerate(groups)
    ]
    timeline_rows = [
        [t["period"], t["commits"], t["contributors"], t["newcomers"], t["truck_factor"], t["year_core_80"]]
        for t in r["timeline"]
    ]
    cohort_rows = [
        [c["year"], c["newcomers"], c["observed"], pct(c["stay_rate"]),
         f"{pct(c['stay_rate_ci95'][0])}–{pct(c['stay_rate_ci95'][1])}" if c["observed"] else "",
         pct(c["one_time_share"])]
        for c in ret["cohorts"]
    ]
    tie_rows = [
        [t["label"].strip(), t["n"], t["stayed"], pct(t["rate"]), f"{pct(t['lo'])}–{pct(t['hi'])}"]
        for t in payload["ties"] + payload["peers"]
    ]
    brokers = ", ".join(b["person"] for b in cur["brokers"][:3])
    network_note = (
        f"{_network_size(n)} (modularity {n['modularity']:.2f})"
        + (f"; a core of {n['core_size']} fits the core–periphery model with ρ = {n['core_fit']:.2f}" if n["core_size"] else "")
        + (f". Main bridges between groups: {brokers}." if brokers else ".")
    ) if n["ties"] else "Nobody shared files with anyone else in the last 12 months."
    findings_html = "".join(f"<li>{esc(f)}</li>" for f in findings(r))
    bots = ", ".join(list(h["bot_identities"])[:6]) or "none"
    ai = ", ".join(h["ai_identities"]) or "none"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(r['repo'])} community health</title>
<style>{(_ASSETS / 'report.css').read_text()}</style>
</head>
<body>
<main>
<header>
  <p class="eyebrow">Open-source community health</p>
  <h1>{esc(r['repo'])}</h1>
  <p class="lede">{h['commits']:,} commits by {h['people']:,} people, {esc(h['first_commit'])} to {esc(h['last_commit'])}.
  “Last 12 months” means the year up to the latest commit ({esc(cur['window']['start'])} to {esc(cur['window']['end'])}).</p>
</header>

<section class="tiles" aria-label="Headline numbers">{tiles}</section>

<section>
  <h2>What stands out</h2>
  <ul class="findings">{findings_html}</ul>
</section>

<section>
  <h2>Who shows up</h2>
  <p class="caption">Contributors each {period}, split into people making their first commit and people who had committed before.</p>
  <figure class="chart" id="chart-activity" aria-label="Contributors per {period}, newcomers and returning"></figure>
  <details><summary>Table</summary>{_table(['Period', 'Commits', 'Contributors', 'Newcomers', 'Truck factor', 'People doing 80%'], timeline_rows, {1, 2, 3, 4, 5})}</details>
</section>

<section>
  <h2>How concentrated is the work</h2>
  <div class="pair">
    <div>
      <h3>Truck factor</h3>
      <p class="caption">Fewest people whose departure would leave more than half the files without a main author, using all history up to each {period}.</p>
      <figure class="chart" id="chart-truck" aria-label="Truck factor over time"></figure>
    </div>
    <div>
      <h3>People making 80% of commits</h3>
      <p class="caption">Smallest group responsible for 80% of commits in the 12 months up to each {period}.</p>
      <figure class="chart" id="chart-core" aria-label="People making 80% of commits over time"></figure>
    </div>
  </div>
  <h3>Truck-factor people</h3>
  {_table(['Person', 'Files authored', 'Share of files', 'Last commit', 'Status'], tf_rows, {1, 2}) if tf_rows else '<p class="caption">No files have a main author.</p>'}
  <p class="caption">{pct(k['single_author_share'])} of the {k['files']:,} tracked files have a single main author. For {pct(k['authors_gone_share'])}, every main author has gone a year without committing.</p>
</section>

<section>
  <h2>The collaboration network, last 12 months</h2>
  <p class="caption">People are linked when they changed the same files or co-authored a commit; thicker ties mean more shared work. Dot size shows commits. Colors mark the three largest communities found by the Louvain method. Core members (the people doing 80% of the work) are named.</p>
  <figure class="chart network" id="chart-network" aria-label="Collaboration network"></figure>
  <p class="caption">{esc(network_note)}</p>
  <details><summary>Communities</summary>{_table(['Group', 'People', 'Most active members'], community_rows, {1})}</details>
  <h3>Most active contributors</h3>
  {_table(['Person', 'Commits, last 12 months', 'Commits, all time', 'First commit', 'Core'], contributor_rows, {1, 2})}
</section>

<section>
  <h2>Do newcomers stay?</h2>
  <p class="caption">Share of each year's newcomers who committed again {stay_window(ret['horizon_days'])}. Newcomers too recent to judge are left out.</p>
  <figure class="chart" id="chart-cohorts" aria-label="Newcomer stay rate by year joined"></figure>
  <details><summary>Table</summary>{_table(['Year joined', 'Newcomers', 'Observed', 'Stayed a year', '95% interval', 'Single commit'], cohort_rows, {0, 1, 2, 3, 5})}</details>

  <h3>Early ties and staying</h3>
  <p class="caption">Did newcomers whose first {s['early_days']} days of work touched the same files as the core team (from {s['peer_lookback_days']} days before they joined) stay longer? Dots are stay rates; lines are 95% intervals. This shows association, not cause.</p>
  <figure class="chart" id="chart-ties" aria-label="Stay rates by early ties to the core"></figure>
  <h3>Stay rate by number of early peers</h3>
  <figure class="chart" id="chart-peers" aria-label="Stay rates by number of early peers"></figure>
  <details><summary>Table</summary>{_table(['Group', 'Newcomers', 'Stayed', 'Stay rate', '95% interval'], tie_rows, {1, 2, 3})}</details>
</section>

<section class="methods">
  <h2>How this was measured</h2>
  <ul>
    <li><strong>Data.</strong> Non-merge commits on the default branch. Identities that share a name or email are merged. Bots ({esc(bots)}) and AI assistants ({esc(ai)}) are not counted as people. Lockfiles, vendored code, changelogs and contributor lists are ignored, and commits touching more than {s['max_files']} files count only as file creations.</li>
    <li><strong>Truck factor.</strong> Avelino et al. (2016): main authors of each file come from the degree-of-authorship model (Fritz et al. 2014); the truck factor is the fewest people whose removal leaves over half the files without one.</li>
    <li><strong>Network.</strong> Each shared file adds 1/(n−1) to the tie between each pair of its n editors (Newman 2001); files with more than {s['max_editors']} editors are skipped. Communities: Louvain. Core–periphery: Borgatti and Everett's discrete model, fitted over people ranked by tie strength.</li>
    <li><strong>Newcomers.</strong> Someone stays if they commit at least once {stay_window(ret['horizon_days'])}; a fixed window gives every cohort the same chance. The core for each newcomer is the group that made 80% of commits in the year before they joined.</li>
    <li><strong>Limits.</strong> Git only records accepted work, so rejected contributions, reviews, and issue discussion are invisible. Sharing a file is a proxy for working together, and file-based authorship misses maintainers who know code they did not write.</li>
  </ul>
  <p class="caption">Generated by ossnet {__version__} on {esc(r['generated'])} from commit {esc(r['head'][:12])}.</p>
</section>
</main>
<script type="application/json" id="ossnet-data">{data}</script>
<script>{(_ASSETS / 'report.js').read_text()}</script>
</body>
</html>
"""
