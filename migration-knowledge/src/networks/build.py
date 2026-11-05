"""Construct the three network layers on a common node set.

Conventions (tested in ``tests/test_networks.py``):

* ``G_migration``: directed; ``W[i, j]`` = people born in node i living in node j.
* ``G_scholars``: directed; ``W[i, j]`` = inferred scholarly moves from i to j.
* ``G_collaboration``: undirected; ``W[i, j] == W[j, i]`` = co-authored works.

Matrices are dense ``numpy`` arrays indexed by a sorted list of ISO3 codes; the
diagonal is always zero (domestic links are not part of any layer).
"""
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd


@dataclass
class Layer:
    name: str
    nodes: list[str]
    W: np.ndarray
    directed: bool
    unit: str

    @property
    def index(self) -> dict[str, int]:
        return {n: i for i, n in enumerate(self.nodes)}

    def edges(self) -> pd.DataFrame:
        """Long edge list with zeros dropped. Undirected layers list i<j once."""
        n = len(self.nodes)
        ii, jj = np.nonzero(self.W)
        if not self.directed:
            keep = ii < jj
            ii, jj = ii[keep], jj[keep]
        return pd.DataFrame({"source": [self.nodes[i] for i in ii],
                             "target": [self.nodes[j] for j in jj],
                             "weight": self.W[ii, jj]})

    def to_networkx(self) -> nx.Graph:
        G = nx.DiGraph() if self.directed else nx.Graph()
        G.add_nodes_from(self.nodes)
        for r in self.edges().itertuples(index=False):
            G.add_edge(r.source, r.target, weight=float(r.weight))
        return G

    def symmetrized(self) -> "Layer":
        """Undirected version (W + W^T) for comparisons with co-authorship."""
        if not self.directed:
            return self
        return Layer(self.name + "_sym", self.nodes, self.W + self.W.T, False, self.unit)

    def restrict(self, nodes: list[str]) -> "Layer":
        idx = [self.index[n] for n in nodes]
        return Layer(self.name, list(nodes), self.W[np.ix_(idx, idx)].copy(), self.directed, self.unit)


def directed_layer(df: pd.DataFrame, nodes: list[str], src: str, dst: str, weight: str,
                   name: str, unit: str) -> Layer:
    """Build a directed layer; rows whose endpoints are outside ``nodes`` are
    dropped. Duplicate (src, dst) rows are summed. Self-loops are dropped."""
    nodes = sorted(nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    W = np.zeros((len(nodes), len(nodes)), dtype=float)
    sub = df[df[src].isin(idx) & df[dst].isin(idx) & (df[src] != df[dst])]
    agg = sub.groupby([src, dst], as_index=False)[weight].sum()
    W[agg[src].map(idx).to_numpy(), agg[dst].map(idx).to_numpy()] = agg[weight].to_numpy(dtype=float)
    return Layer(name, nodes, W, True, unit)


def undirected_layer(df: pd.DataFrame, nodes: list[str], a: str, b: str, weight: str,
                     name: str, unit: str) -> Layer:
    """Build an undirected layer from rows that each describe one unordered
    pair. Rows listing the same pair in both orders are an error (it would
    double count), so callers must canonicalize pairs first."""
    nodes = sorted(nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    sub = df[df[a].isin(idx) & df[b].isin(idx) & (df[a] != df[b])].copy()
    lo = np.where(sub[a] < sub[b], sub[a], sub[b])
    hi = np.where(sub[a] < sub[b], sub[b], sub[a])
    sub = sub.assign(_lo=lo, _hi=hi)
    if sub.duplicated(["_lo", "_hi"]).any():
        dups = sub[sub.duplicated(["_lo", "_hi"], keep=False)][["_lo", "_hi"]].head()
        raise ValueError(f"undirected input lists some pairs more than once, e.g.\n{dups}")
    W = np.zeros((len(nodes), len(nodes)), dtype=float)
    i = sub["_lo"].map(idx).to_numpy()
    j = sub["_hi"].map(idx).to_numpy()
    w = sub[weight].to_numpy(dtype=float)
    W[i, j] = w
    W[j, i] = w
    return Layer(name, nodes, W, False, unit)


def canonical_pairs(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    """Return df with columns ``a``/``b`` reordered so a < b (lexicographic)."""
    lo = np.where(df[a] < df[b], df[a], df[b])
    hi = np.where(df[a] < df[b], df[b], df[a])
    return df.assign(**{a: lo, b: hi})
