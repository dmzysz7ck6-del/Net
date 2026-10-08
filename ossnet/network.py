"""Collaboration networks built from who changed which files."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

import networkx as nx

from .history import Commit


def collaboration_graph(commits: Iterable[Commit], *, max_editors: int = 50) -> nx.Graph:
    """Link people who changed the same files, or who co-authored a commit.

    Each shared file adds 1/(n-1) to the tie between every pair of its n
    editors (Newman's weighting for collaboration networks), so a file two
    people shared counts for more than one touched by ten. Bulk commits and
    files with more than `max_editors` editors add no ties. Each co-authored
    commit adds 1 to the tie between its authors. Nodes carry a `commits`
    count.
    """
    G = nx.Graph()
    editors: dict[int, set[str]] = defaultdict(set)
    for c in commits:
        for a in c.authors:
            if a in G:
                G.nodes[a]["commits"] += 1
            else:
                G.add_node(a, commits=1)
        for a, b in combinations(c.authors, 2):
            _add_weight(G, a, b, 1.0)
        if not c.bulk:
            for f in c.files:
                editors[f].update(c.authors)
    for people in editors.values():
        if 2 <= len(people) <= max_editors:
            w = 1.0 / (len(people) - 1)
            for a, b in combinations(sorted(people), 2):
                _add_weight(G, a, b, w)
    return G


def _add_weight(G: nx.Graph, a: str, b: str, w: float) -> None:
    if G.has_edge(a, b):
        G[a][b]["weight"] += w
    else:
        G.add_edge(a, b, weight=w)


@dataclass(frozen=True)
class CorePeriphery:
    core: list[str]
    rho: float  # correlation with an ideal core/periphery pattern, -1..1


def core_periphery(G: nx.Graph) -> CorePeriphery | None:
    """Fit Borgatti and Everett's discrete core/periphery model.

    The ideal pattern has every core pair tied and no periphery pair tied;
    core-periphery pairs are ignored. Rather than searching all partitions,
    people are ranked by tie strength and every split of that ranking is
    scored, a standard fast approximation (cf. Lip 2011). Incremental edge
    counts keep this O(n + m). Returns None for graphs too small to have
    both a core and a periphery.
    """
    n = G.number_of_nodes()
    if n < 4 or G.number_of_edges() == 0:
        return None
    order = sorted(G, key=lambda v: (-G.degree(v, weight="weight"), -G.degree(v), str(v)))
    rank = {v: i for i, v in enumerate(order)}
    core_edges, periphery_edges = 0, G.number_of_edges()
    best_k, best_rho = 0, -math.inf
    for k in range(1, n - 1):  # core = order[:k]
        v = order[k - 1]
        core_edges += sum(1 for u in G[v] if rank[u] < k - 1)
        periphery_edges -= sum(1 for u in G[v] if rank[u] > k - 1)
        if k < 2:
            continue
        rho = _pattern_correlation(n, k, core_edges, periphery_edges)
        if rho > best_rho:
            best_k, best_rho = k, rho
    if best_k == 0:
        return None
    return CorePeriphery(core=order[:best_k], rho=best_rho)


def _pattern_correlation(n: int, k: int, core_edges: int, periphery_edges: int) -> float:
    """Pearson correlation, over core-core and periphery-periphery pairs,
    between observed ties and the ideal pattern (1 in the core, 0 outside)."""
    core_pairs = k * (k - 1) // 2
    pairs = core_pairs + (n - k) * (n - k - 1) // 2
    ties = core_edges + periphery_edges
    denom = ties * (pairs - ties) * core_pairs * (pairs - core_pairs)
    if denom <= 0:
        return 0.0
    return (pairs * core_edges - ties * core_pairs) / math.sqrt(denom)


def network_stats(G: nx.Graph, *, seed: int = 0) -> dict:
    """Size, cohesion, community structure and core/periphery fit."""
    n, m = G.number_of_nodes(), G.number_of_edges()
    stats = {
        "people": n,
        "ties": m,
        "density": nx.density(G) if n > 1 else 0.0,
        "isolated": nx.number_of_isolates(G),
        "largest_group_share": None,
        "clustering": None,
        "communities": None,
        "modularity": None,
        "core_size": None,
        "core_fit": None,
    }
    if m == 0:
        return stats
    stats["largest_group_share"] = max(len(c) for c in nx.connected_components(G)) / n
    stats["clustering"] = nx.average_clustering(G)
    groups = communities(G, seed=seed)
    stats["communities"] = sum(1 for g in groups if len(g) > 1)
    stats["modularity"] = nx.community.modularity(G, groups, weight="weight")
    cp = core_periphery(G)
    if cp:
        stats["core_size"], stats["core_fit"] = len(cp.core), cp.rho
    return stats


def communities(G: nx.Graph, *, seed: int = 0) -> list[set[str]]:
    """Louvain communities, largest first."""
    groups = nx.community.louvain_communities(G, weight="weight", seed=seed)
    return sorted(groups, key=lambda g: (-len(g), sorted(g)[0]))


def layout(G: nx.Graph, *, seed: int = 0, per_row: int = 20) -> dict[str, tuple[float, float]]:
    """Positions in the unit square for drawing G.

    The largest connected group gets a spring layout. Everyone else (small
    groups and people with no ties) sits in rows along the bottom, so they
    don't push the main group into a corner.
    """
    if len(G) == 0:
        return {}
    groups = sorted(nx.connected_components(G), key=lambda g: (-len(g), min(g)))
    main = groups[0] if len(groups[0]) > 1 else set()
    rest = [
        v for g in groups if g is not main
        for v in sorted(g, key=lambda v: (-G.nodes[v].get("commits", 0), v))
    ]
    if not main:
        per_row = math.ceil(math.sqrt(len(rest) * 1.6))
    rows = math.ceil(len(rest) / per_row)
    strip = (min(0.35, 0.09 * rows) if main else 1.0) if rest else 0.0

    pos: dict[str, tuple[float, float]] = {}
    if main:
        raw = nx.spring_layout(G.subgraph(main), weight="weight", seed=seed, iterations=300)
        xs, ys = [p[0] for p in raw.values()], [p[1] for p in raw.values()]
        height = 1.0 - strip - (0.06 if rest else 0.0)
        for v, (x, y) in raw.items():
            pos[v] = (_unit(x, xs), _unit(y, ys) * height)
    for i, v in enumerate(rest):
        row, col = divmod(i, per_row)
        y = 1.0 - strip + (row + 0.5) * strip / rows
        pos[v] = ((col + 0.5) / per_row, y)
    return pos


def _unit(v: float, values: list[float]) -> float:
    lo, hi = min(values), max(values)
    return 0.5 if hi == lo else (v - lo) / (hi - lo)


def brokers(G: nx.Graph, top: int = 5, *, seed: int = 0) -> list[tuple[str, float]]:
    """People who sit on the most shortest paths between others (betweenness).

    Stronger ties count as shorter distances. Large graphs use a sampled
    estimate."""
    if G.number_of_edges() == 0:
        return []
    H = G.copy()
    for _, _, d in H.edges(data=True):
        d["distance"] = 1.0 / d["weight"]
    sample = None if len(H) <= 400 else 400
    scores = nx.betweenness_centrality(H, k=sample, weight="distance", seed=seed)
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(p, s) for p, s in ranked[:top] if s > 0]
