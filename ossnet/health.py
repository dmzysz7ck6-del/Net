"""Community-health measures computed from a `History`."""

from __future__ import annotations

import bisect
import math
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

import networkx as nx

from .history import Commit, History
from .network import brokers, collaboration_graph, communities, core_periphery, layout, network_stats

DAY = 86400
YEAR = 365 * DAY


def gini(values) -> float:
    """0 when everyone contributes equally, near 1 when one person does it all."""
    xs = sorted(v for v in values if v > 0)
    n, total = len(xs), sum(xs)
    if n < 2:
        return 0.0
    return 2 * sum(i * x for i, x in enumerate(xs, 1)) / (n * total) - (n + 1) / n


def core_by_share(counts: Counter, share: float = 0.8) -> list[str]:
    """Smallest group of people who together made `share` of the contributions."""
    target = share * sum(counts.values()) - 1e-9
    core, running = [], 0
    for person, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        if running >= target:
            break
        core.append(person)
        running += n
    return core


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | tuple[None, None]:
    """95% Wilson score interval for a proportion k/n."""
    if n == 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


class Knowledge:
    """Who knows which files, by degree of authorship (Fritz et al. 2014),
    the model behind Avelino et al.'s (2016) truck-factor algorithm.

    DOA = 3.293 + 1.098*FA + 0.164*DL - 0.321*ln(1 + AC), where FA is 1 for
    the file's creator, DL counts the person's edits to it, and AC counts
    everyone else's. A person is an author of a file when their DOA is at
    least 3.293 and above 75% of the file's top score. Commits are credited
    to their main author; bulk commits count only for creating files.
    """

    def __init__(self) -> None:
        self.creator: dict[int, str] = {}
        self.edits: dict[int, Counter] = defaultdict(Counter)
        self.seen: set[int] = set()
        self.dead: set[int] = set()

    def apply(self, c: Commit) -> None:
        self.seen.update(c.files)
        self.dead.update(c.deleted)
        if not c.authors:
            return
        author = c.authors[0]
        for f in c.created:
            self.creator[f] = author
        if not c.bulk:
            for f in c.files:
                self.edits[f][author] += 1

    def authors(self) -> dict[int, set[str]]:
        """Authors of every live file that some person has been credited with."""
        result = {}
        for f in self.seen - self.dead:
            edits = self.edits.get(f, Counter())
            creator = self.creator.get(f)
            people = set(edits) | ({creator} if creator else set())
            if not people:
                continue
            total = sum(edits.values())
            doa = {
                p: 3.293 + 1.098 * (p == creator) + 0.164 * edits[p] - 0.321 * math.log1p(total - edits[p])
                for p in people
            }
            top = max(doa.values())
            result[f] = {p for p, v in doa.items() if v >= 3.293 and v > 0.75 * top}
        return result


def truck_factor(authors: dict[int, set[str]], threshold: float = 0.5) -> list[str]:
    """The fewest people whose departure would leave more than `threshold` of
    the files without any author (Avelino et al. 2016): remove the person who
    authors the most files, repeat until the threshold is crossed."""
    files = len(authors)
    owned: dict[str, list[int]] = defaultdict(list)
    for f, people in authors.items():
        for p in people:
            owned[p].append(f)
    remaining = {f: len(people) for f, people in authors.items()}
    orphans = sum(1 for n in remaining.values() if n == 0)
    removed = []
    for person in sorted(owned, key=lambda p: (-len(owned[p]), p)):
        if orphans > threshold * files:
            break
        removed.append(person)
        for f in owned[person]:
            remaining[f] -= 1
            if remaining[f] == 0:
                orphans += 1
    return removed


@dataclass(frozen=True)
class Period:
    label: str
    start: int
    end: int


def periods(first: int, last: int, unit: str = "quarter") -> list[Period]:
    """Calendar periods (UTC) covering first..last."""
    step = {"month": 1, "quarter": 3, "year": 12}[unit]
    dt = datetime.fromtimestamp(first, timezone.utc)
    year, month = dt.year, (dt.month - 1) // step * step  # month is zero-based
    out = []
    while True:
        start = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        year, month = year + (month + step) // 12, (month + step) % 12
        end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        if unit == "year":
            label = f"{start.year}"
        elif unit == "quarter":
            label = f"{start.year} Q{start.month // 3 + 1}"
        else:
            label = f"{start.year}-{start.month:02d}"
        out.append(Period(label, int(start.timestamp()), int(end.timestamp())))
        if end.timestamp() > last:
            return out


def contributor_stats(commits: list[Commit]) -> dict[str, dict]:
    """Commit times and counts for every person."""
    stats: dict[str, dict] = {}
    for c in commits:
        for i, person in enumerate(c.authors):
            s = stats.setdefault(person, {"times": [], "commits": 0, "coauthored": 0})
            s["times"].append(c.time)
            s["commits"] += 1
            s["coauthored"] += i > 0
    for s in stats.values():
        s["times"].sort()
        s["first"], s["last"] = s["times"][0], s["times"][-1]
    return stats


def stayed(s: dict, horizon: int = YEAR) -> bool:
    """Did this person commit in their second `horizon` (by default 12 to 24
    months after their first commit)? A fixed window gives every cohort the
    same chance, however long ago they joined."""
    i = bisect.bisect_left(s["times"], s["first"] + horizon)
    return i < len(s["times"]) and s["times"][i] < s["first"] + 2 * horizon


def timeline(commits: list[Commit], unit: str = "quarter", *, trailing: int = YEAR,
             max_editors: int = 50, seed: int = 0) -> list[dict]:
    """One row per period: activity in the period, concentration and network
    structure over the trailing year, and the truck factor of the history so
    far. `commits` must be sorted by time."""
    human = [c for c in commits if c.authors]
    if not human:
        return []
    times = [c.time for c in commits]
    joined = sorted(s["first"] for s in contributor_stats(human).values())
    now = time.time()
    knowledge, applied, rows = Knowledge(), 0, []
    for p in periods(human[0].time, human[-1].time, unit):
        lo, hi = bisect.bisect_left(times, p.start), bisect.bisect_left(times, p.end)
        while applied < hi:
            knowledge.apply(commits[applied])
            applied += 1
        recent = commits[bisect.bisect_left(times, p.end - trailing):hi]
        counts = Counter(a for c in recent for a in c.authors)
        net = network_stats(collaboration_graph(recent, max_editors=max_editors), seed=seed)
        rows.append({
            "period": p.label,
            "start": _iso(p.start),
            "in_progress": p.end > now,
            "commits": sum(1 for c in commits[lo:hi] if c.authors),
            "assisted_commits": sum(1 for c in commits[lo:hi] if c.assisted),
            "contributors": len({a for c in commits[lo:hi] for a in c.authors}),
            "newcomers": bisect.bisect_left(joined, p.end) - bisect.bisect_left(joined, p.start),
            "year_contributors": len(counts),
            "year_core_80": len(core_by_share(counts)) if counts else 0,
            "year_top_share": max(counts.values()) / sum(counts.values()) if counts else None,
            "year_gini": gini(counts.values()),
            "truck_factor": len(truck_factor(knowledge.authors())),
            **{f"year_network_{k}": v for k, v in net.items()},
        })
    return rows


def retention(stats: dict[str, dict], data_end: int, horizon: int = YEAR) -> dict:
    """How many newcomers stayed (see `stayed`), by the year they joined.
    Only people who joined at least two horizons before the end of the data
    can be judged."""
    cohorts: dict[int, Counter] = defaultdict(Counter)
    for s in stats.values():
        row = cohorts[datetime.fromtimestamp(s["first"], timezone.utc).year]
        row["newcomers"] += 1
        if s["first"] <= data_end - 2 * horizon:
            row["observed"] += 1
            row["stayed"] += stayed(s, horizon)
            row["one_time"] += s["commits"] == 1
    total = sum(cohorts.values(), Counter())

    def describe(row: Counter, **extra) -> dict:
        observed = row["observed"]
        lo, hi = wilson(row["stayed"], observed)
        return {
            **extra,
            "newcomers": row["newcomers"],
            "observed": observed,
            "stayed": row["stayed"],
            "stay_rate": row["stayed"] / observed if observed else None,
            "stay_rate_ci95": [lo, hi],
            "one_time_share": row["one_time"] / observed if observed else None,
        }

    return {
        "horizon_days": horizon // DAY,
        "overall": describe(total),
        "cohorts": [describe(cohorts[y], year=y) for y in sorted(cohorts)],
    }


def newcomer_ties(commits: list[Commit], stats: dict[str, dict], data_end: int, *,
                  early: int = 90 * DAY, peer_lookback: int = 30 * DAY,
                  horizon: int = YEAR) -> list[dict]:
    """For each newcomer, did their first `early` days of work connect them to
    the project's core, and did they stay (see `stayed`)?

    A newcomer's early peers are their co-authors plus everyone who changed
    the same files from `peer_lookback` before they joined until the end of
    their early window. The core is the smallest group that made 80% of the
    commits in the year before they joined. Newcomers who joined a project
    nobody else was active in, or too recently to judge, are skipped.
    `commits` must be sorted by time.
    """
    times = [c.time for c in commits]
    edits: dict[int, list[tuple[int, tuple[str, ...]]]] = defaultdict(list)
    mine: dict[str, list[Commit]] = defaultdict(list)
    for c in commits:
        for a in c.authors:
            mine[a].append(c)
        if c.authors and not c.bulk:
            for f in c.files:
                edits[f].append((c.time, c.authors))
    edit_times = {f: [t for t, _ in rows] for f, rows in edits.items()}

    rows = []
    for person, s in stats.items():
        t0 = s["first"]
        if t0 > data_end - 2 * horizon:
            continue
        before = commits[bisect.bisect_left(times, t0 - YEAR):bisect.bisect_left(times, t0)]
        counts = Counter(a for c in before for a in c.authors if a != person)
        if not counts:
            continue
        core = set(core_by_share(counts))
        first_work = [c for c in mine[person] if c.time < t0 + early]
        files = {f for c in first_work if not c.bulk for f in c.files}
        peers = {a for c in first_work for a in c.authors}
        for f in files:
            ts = edit_times[f]
            lo, hi = bisect.bisect_left(ts, t0 - peer_lookback), bisect.bisect_left(ts, t0 + early)
            for _, authors in edits[f][lo:hi]:
                peers.update(authors)
        peers.discard(person)
        rows.append({
            "person": person,
            "joined": _iso(t0),
            "early_commits": len(first_work),
            "early_files": len(files),
            "early_peers": len(peers),
            "early_core_peers": len(peers & core),
            "tied_to_core": bool(peers & core),
            "stayed": stayed(s, horizon),
        })
    return rows


PEER_BINS = (("0", 0, 0), ("1", 1, 1), ("2-4", 2, 4), ("5+", 5, math.inf))


def tie_effect(rows: list[dict]) -> dict:
    """Stay rates for newcomers with and without early ties to the core,
    overall and split by how much they did in their first weeks, plus stay
    rates by how many early peers they had."""

    def rate(group: list[dict]) -> dict:
        n, k = len(group), sum(r["stayed"] for r in group)
        return {"newcomers": n, "stayed": k, "stay_rate": k / n if n else None, "ci95": list(wilson(k, n))}

    def split(group: list[dict]) -> dict:
        return {
            "all": rate(group),
            "tied": rate([r for r in group if r["tied_to_core"]]),
            "not_tied": rate([r for r in group if not r["tied_to_core"]]),
        }

    return {
        **split(rows),
        "by_early_commits": {
            "1": split([r for r in rows if r["early_commits"] == 1]),
            "2+": split([r for r in rows if r["early_commits"] >= 2]),
        },
        "by_early_peers": {
            label: rate([r for r in rows if lo <= r["early_peers"] <= hi]) for label, lo, hi in PEER_BINS
        },
    }


def snapshot(G: nx.Graph, core: set[str], groups: list[set[str]], *, limit: int = 150,
             seed: int = 7) -> dict:
    """Positions for drawing the most active part of a collaboration network."""
    keep = sorted(G, key=lambda v: (-G.nodes[v]["commits"], v))[:limit]
    H = G.subgraph(keep)
    pos = layout(H, seed=seed)
    group_of = {v: i for i, g in enumerate(groups) if len(g) > 1 for v in g}
    parts = sorted(nx.connected_components(H), key=lambda g: (-len(g), min(g)))  # same order as layout()
    main = parts[0] if parts and len(parts[0]) > 1 else set()
    return {
        "shown": len(H),
        "total": len(G),
        "nodes": [
            {
                "id": v,
                "commits": H.nodes[v]["commits"],
                "community": group_of.get(v),
                "core": v in core,
                "main": v in main,
                "x": round(pos[v][0], 4),
                "y": round(pos[v][1], 4),
            }
            for v in keep
        ],
        "edges": [{"source": a, "target": b, "weight": d["weight"]} for a, b, d in H.edges(data=True)],
    }


def analyze(history: History, *, unit: str = "quarter", horizon_days: int = 365,
            early_days: int = 90, peer_lookback_days: int = 30, max_editors: int = 50,
            seed: int = 0) -> dict:
    """Everything the CLI reports, as plain JSON-ready data."""
    commits = sorted(history.commits, key=lambda c: c.time)
    human = [c for c in commits if c.authors]
    if not human:
        raise ValueError("no human commits to analyze")
    horizon = horizon_days * DAY
    data_end = human[-1].time
    stats = contributor_stats(human)

    times = [c.time for c in commits]
    recent = commits[bisect.bisect_left(times, data_end - YEAR + 1):]
    counts = Counter(a for c in recent for a in c.authors)
    G = collaboration_graph(recent, max_editors=max_editors)
    groups = communities(G, seed=seed) if G.number_of_edges() else []
    cp = core_periphery(G)
    core_80 = core_by_share(counts)

    ties = newcomer_ties(human, stats, data_end, early=early_days * DAY,
                         peer_lookback=peer_lookback_days * DAY, horizon=horizon)
    return {
        "repo": history.repo,
        "head": history.head,
        "generated": _iso(int(time.time())),
        "settings": {
            "period": unit,
            "horizon_days": horizon_days,
            "early_days": early_days,
            "peer_lookback_days": peer_lookback_days,
            "max_editors": max_editors,
            "max_files": history.max_files,
        },
        "history": {
            "first_commit": _iso(human[0].time),
            "last_commit": _iso(data_end),
            "days_since_last_commit": int((time.time() - data_end) // DAY),
            "commits": len(human),
            "people": len(stats),
            "commits_without_people": sum(1 for c in commits if not c.authors),
            "bot_identities": dict(history.bots.most_common()),
            "ai_identities": dict(history.assistants.most_common()),
        },
        "current": {
            "window": {"start": _iso(data_end - YEAR + 1), "end": _iso(data_end)},
            "commits": sum(1 for c in recent if c.authors),
            "assisted_share": (
                sum(c.assisted for c in recent) / max(1, sum(1 for c in recent if c.authors or c.assisted))
            ),
            "contributors": len(counts),
            "newcomers": sum(1 for s in stats.values() if s["first"] > data_end - YEAR),
            "core_80": core_80,
            "top_contributor": (
                {"person": core_80[0], "share": counts[core_80[0]] / sum(counts.values())} if core_80 else None
            ),
            "gini": gini(counts.values()),
            "knowledge": _knowledge_summary(commits, stats, data_end),
            "network": network_stats(G, seed=seed),
            "network_core": cp.core if cp else [],
            "brokers": [{"person": p, "betweenness": b} for p, b in brokers(G, seed=seed)],
            "communities": [sorted(g, key=lambda v: (-G.nodes[v]["commits"], v)) for g in groups if len(g) > 1],
        },
        "retention": retention(stats, data_end, horizon),
        "newcomer_ties": tie_effect(ties),
        "timeline": timeline(commits, unit, max_editors=max_editors, seed=seed),
        "contributors": [
            {
                "person": p,
                "first": _iso(s["first"]),
                "last": _iso(s["last"]),
                "commits": s["commits"],
                "commits_last_year": counts.get(p, 0),
                "coauthored": s["coauthored"],
                "active_last_year": p in counts,
                "core_80": p in core_80,
                "aliases": history.aliases.get(p, []),
            }
            for p, s in sorted(stats.items(), key=lambda kv: (-kv[1]["commits"], kv[0]))
        ],
        "newcomers": ties,
        "snapshot": snapshot(G, set(core_80), groups, seed=seed + 7),
    }


def _knowledge_summary(commits: list[Commit], stats: dict[str, dict], data_end: int) -> dict:
    """Truck factor at HEAD, plus how much know-how may already have walked
    away: files whose authors have all gone a year without committing (cf.
    Rigby et al. 2016 on turnover-induced knowledge loss)."""
    knowledge = Knowledge()
    for c in commits:
        knowledge.apply(c)
    authors = knowledge.authors()
    files = len(authors)
    tf = truck_factor(authors)
    authored = Counter(p for people in authors.values() for p in people)
    active = {p for p, s in stats.items() if s["last"] > data_end - YEAR}

    def share(n: int) -> float | None:
        return n / files if files else None

    return {
        "files": files,
        "truck_factor": len(tf),
        "truck_factor_people": [
            {"person": p, "files": authored[p], "share": share(authored[p]),
             "last_commit": _iso(stats[p]["last"]), "active": p in active}
            for p in tf
        ],
        "single_author_share": share(sum(1 for people in authors.values() if len(people) == 1)),
        "no_author_share": share(sum(1 for people in authors.values() if not people)),
        "authors_gone_share": share(sum(1 for people in authors.values() if people and not people & active)),
    }


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")
