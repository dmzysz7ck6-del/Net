import math
import random
from collections import Counter

import networkx as nx
import pytest

from ossnet.health import (
    DAY, YEAR, Knowledge, contributor_stats, core_by_share, gini, newcomer_ties, periods, retention,
    stayed, tie_effect, truck_factor, wilson,
)
from ossnet.history import Commit
from ossnet.network import _pattern_correlation, collaboration_graph, core_periphery, layout


def commit(t, authors, files=(), created=(), deleted=(), bulk=False):
    return Commit(sha=f"{t}", time=int(t), authors=tuple(authors), files=tuple(files),
                  created=tuple(created), deleted=tuple(deleted), bulk=bulk)


def test_gini():
    assert gini([5, 5, 5]) == 0
    assert gini([1, 3]) == pytest.approx(0.25)
    assert gini([7]) == 0


def test_core_by_share():
    assert core_by_share(Counter(a=8, b=1, c=1)) == ["a"]
    assert core_by_share(Counter(a=5, b=3, c=2)) == ["a", "b"]
    assert core_by_share(Counter()) == []


def test_wilson_interval_brackets_the_rate():
    lo, hi = wilson(5, 50)
    assert lo < 0.1 < hi
    assert wilson(0, 0) == (None, None)


def test_truck_factor_removes_top_authors_until_most_files_are_orphaned():
    authors = {1: {"A"}, 2: {"A"}, 3: {"A"}, 4: {"B"}, 5: {"B"}, 6: {"C"}}
    assert truck_factor(authors) == ["A", "B"]  # removing A orphans exactly half: not enough
    assert truck_factor({1: {"A"}, 2: {"A"}, 3: {"A"}, 4: {"B"}}) == ["A"]
    assert truck_factor({1: set(), 2: set(), 3: {"A"}}) == []
    assert truck_factor({}) == []


def test_degree_of_authorship():
    k = Knowledge()
    k.apply(commit(0, ["A"], files=[1], created=[1]))
    for t in range(1, 11):
        k.apply(commit(t, ["B"], files=[1]))
    # A: 3.293 + 1.098 + 0.164 - 0.321 ln 11 = 3.785; B: 3.293 + 1.64 - 0.321 ln 2 = 4.711
    assert k.authors() == {1: {"A", "B"}}  # 3.785 / 4.711 = 0.80 > 0.75
    for t in range(11, 21):
        k.apply(commit(t, ["B"], files=[1]))
    assert k.authors() == {1: {"B"}}


def test_knowledge_ignores_deleted_files_and_bulk_edits():
    k = Knowledge()
    k.apply(commit(0, ["A"], files=[1, 2], created=[1, 2]))
    k.apply(commit(1, ["B"], files=[1], bulk=True))
    k.apply(commit(2, ["A"], deleted=[2]))
    assert k.authors() == {1: {"A"}}


def test_collaboration_graph_uses_newman_weights_and_coauthorship():
    G = collaboration_graph([
        commit(0, ["A"], files=[1, 2]),
        commit(1, ["B"], files=[1, 2]),
        commit(2, ["C"], files=[2]),
        commit(3, ["A", "C"]),
        commit(4, ["D"], files=[1], bulk=True),
    ])
    assert G["A"]["B"]["weight"] == pytest.approx(1.5)  # file 1 (2 editors) + file 2 (3 editors)
    assert G["A"]["C"]["weight"] == pytest.approx(1.5)  # file 2 + one co-authored commit
    assert "D" in G and G.degree("D") == 0  # bulk commits add no ties
    assert G.nodes["A"]["commits"] == 2


def test_core_periphery_finds_a_planted_core():
    G = nx.complete_graph(["a", "b", "c", "d"])
    for i, hub in enumerate("abcd" * 2):
        G.add_edge(hub, f"p{i}")
    nx.set_edge_attributes(G, 1.0, "weight")
    cp = core_periphery(G)
    assert sorted(cp.core) == ["a", "b", "c", "d"]
    assert cp.rho == pytest.approx(1.0)


def test_core_periphery_incremental_counts_match_brute_force():
    rng = random.Random(3)
    G = nx.gnp_random_graph(30, 0.15, seed=4)
    for a, b in G.edges:
        G[a][b]["weight"] = rng.random()
    cp = core_periphery(G)
    order = sorted(G, key=lambda v: (-G.degree(v, weight="weight"), -G.degree(v), str(v)))

    def rho(k):
        return _pattern_correlation(len(G), k, G.subgraph(order[:k]).number_of_edges(),
                                    G.subgraph(order[k:]).number_of_edges())

    best_k = max(range(2, len(G) - 1), key=lambda k: (rho(k), -k))
    assert len(cp.core) == best_k
    assert cp.rho == pytest.approx(rho(best_k))


def test_layout_keeps_everyone_in_the_unit_square():
    G = nx.path_graph(["a", "b", "c"])
    G.add_nodes_from(["x", "y"])
    nx.set_edge_attributes(G, 1.0, "weight")
    pos = layout(G, seed=1)
    assert set(pos) == {"a", "b", "c", "x", "y"}
    assert all(0 <= x <= 1 and 0 <= y <= 1 for x, y in pos.values())
    assert min(pos["x"][1], pos["y"][1]) > max(pos[v][1] for v in "abc")  # loners sit below


def test_periods_cover_the_range():
    first, last = 1_581_724_800, 1_593_561_600  # 2020-02-15, 2020-07-01
    assert [p.label for p in periods(first, last, "quarter")] == ["2020 Q1", "2020 Q2", "2020 Q3"]
    assert [p.label for p in periods(first, first, "year")] == ["2020"]
    assert len(periods(first, last, "month")) == 6


def test_staying_means_committing_in_the_second_year():
    stats = contributor_stats([
        commit(0, ["early"]), commit(400 * DAY, ["early"]),  # back in year two
        commit(0, ["late"]), commit(800 * DAY, ["late"]),  # back only in year three
        commit(0, ["once"]),
    ])
    assert stayed(stats["early"]) and not stayed(stats["late"]) and not stayed(stats["once"])


def test_retention_only_judges_people_with_two_years_of_data():
    commits = [commit(0, ["a"]), commit(400 * DAY, ["a"]), commit(10 * DAY, ["b"]),
               commit(900 * DAY, ["c"])]
    r = retention(contributor_stats(commits), data_end=900 * DAY)
    assert r["overall"]["observed"] == 2  # c joined too recently
    assert r["overall"]["stayed"] == 1
    assert r["overall"]["one_time_share"] == 0.5


def test_newcomer_ties_detect_overlap_with_the_core():
    commits = [commit(t * DAY, ["core"], files=[1]) for t in range(0, 60, 5)]
    commits += [
        commit(70 * DAY, ["joiner"], files=[1]),  # same file the core works on
        commit(500 * DAY, ["joiner"], files=[1]),
        commit(80 * DAY, ["loner"], files=[2]),  # a file nobody else touches
        commit(900 * DAY, ["core"], files=[1]),
    ]
    commits.sort(key=lambda c: c.time)
    stats = contributor_stats(commits)
    rows = {r["person"]: r for r in newcomer_ties(commits, stats, data_end=900 * DAY)}
    assert set(rows) == {"joiner", "loner"}  # the founder had nobody to join
    assert rows["joiner"]["tied_to_core"] and rows["joiner"]["stayed"]
    assert not rows["loner"]["tied_to_core"] and not rows["loner"]["stayed"]
    effect = tie_effect(list(rows.values()))
    assert effect["tied"]["stay_rate"] == 1.0 and effect["not_tied"]["stay_rate"] == 0.0
    assert effect["by_early_peers"]["1"]["newcomers"] == 1
