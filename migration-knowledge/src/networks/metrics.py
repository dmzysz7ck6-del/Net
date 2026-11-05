"""Network measures retained for this study, and why.

* strength (in/out): total connectivity; used only after normalization because
  raw strength mostly measures country size.
* Herfindahl concentration and effective number of partners (1/HHI): how
  concentrated a country's links are.
* extra-regional share and participation coefficient with an exogenous
  partition (UN M49 subregions): bridging relative to geography, defined
  without unstable community detection.
* betweenness on a disparity-filter backbone: brokerage among statistically
  salient links; computed on distances 1/w of normalized weights.
* Louvain communities (seeded) and adjusted mutual information across layers:
  whether layers group countries the same way.
* density / connected components: basic structure, reported for completeness.

Degree-based centralities on the raw (near-complete) weighted graphs are not
reported: in dense layers they mostly re-measure size.
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

from .build import Layer


def strengths(layer: Layer) -> pd.DataFrame:
    W = layer.W
    df = pd.DataFrame({"iso3": layer.nodes, "out_strength": W.sum(1), "in_strength": W.sum(0)})
    if not layer.directed:
        df = df.drop(columns="in_strength").rename(columns={"out_strength": "strength"})
    return df


def concentration(layer: Layer, axis: str = "out") -> pd.DataFrame:
    W = layer.W if axis == "out" else layer.W.T
    s = W.sum(1, keepdims=True)
    P = np.divide(W, s, out=np.zeros_like(W), where=s > 0)
    hhi = (P ** 2).sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ent = -(np.where(P > 0, P * np.log(P), 0.0)).sum(1)
    return pd.DataFrame({"iso3": layer.nodes, f"hhi_{axis}": np.where(s[:, 0] > 0, hhi, np.nan),
                         f"eff_partners_{axis}": np.where(s[:, 0] > 0, 1 / np.where(hhi > 0, hhi, np.nan), np.nan),
                         f"entropy_{axis}": np.where(s[:, 0] > 0, ent, np.nan),
                         f"n_partners_{axis}": (W > 0).sum(1)})


def participation(layer: Layer, partition: dict[str, str], axis: str = "out") -> pd.DataFrame:
    """Extra-group share and participation coefficient P_i = 1 - sum_g (s_ig/s_i)^2."""
    W = layer.W if axis == "out" else layer.W.T
    groups = sorted({partition.get(n, "NA") for n in layer.nodes})
    gi = np.array([groups.index(partition.get(n, "NA")) for n in layer.nodes])
    G = np.zeros((len(layer.nodes), len(groups)))
    for g in range(len(groups)):
        G[:, g] = W[:, gi == g].sum(1)
    s = W.sum(1)
    own = G[np.arange(len(gi)), gi]
    with np.errstate(divide="ignore", invalid="ignore"):
        pc = 1 - ((G / s[:, None]) ** 2).sum(1)
        extra = 1 - own / s
    return pd.DataFrame({"iso3": layer.nodes, f"participation_{axis}": np.where(s > 0, pc, np.nan),
                         f"extra_regional_share_{axis}": np.where(s > 0, extra, np.nan)})


def disparity_backbone(layer: Layer, alpha: float) -> Layer:
    """Serrano, Boguna & Vespignani (2009) disparity filter.

    For node i with k_i > 1 neighbours, edge (i, j) has significance
    a_ij = (1 - p_ij)^(k_i - 1) with p_ij = w_ij / s_i. An edge is kept if it is
    significant (a < alpha) from either endpoint (undirected) or from the
    source's out-perspective or target's in-perspective (directed).
    """
    W = layer.W

    def alpha_matrix(M: np.ndarray) -> np.ndarray:
        s = M.sum(1, keepdims=True)
        k = (M > 0).sum(1, keepdims=True)
        P = np.divide(M, s, out=np.zeros_like(M), where=s > 0)
        A = np.where(M > 0, (1 - P) ** np.maximum(k - 1, 0), 1.0)
        A = np.where((k <= 1) & (M > 0), 0.0, A)  # a node's only link is always kept
        return A

    A_out = alpha_matrix(W)
    A_in = alpha_matrix(W.T).T
    keep = (A_out < alpha) | (A_in < alpha)
    if not layer.directed:
        keep = keep | keep.T
    return Layer(f"{layer.name}_bb{alpha}", layer.nodes, np.where(keep, W, 0.0), layer.directed, layer.unit)


def betweenness(layer: Layer, normalize_by_strength: bool = True) -> pd.DataFrame:
    """Weighted betweenness with distance = 1 / w_norm.

    ``w_norm = w_ij / sqrt(s_i s_j)`` removes the mechanical advantage of large
    countries before shortest paths are computed.
    """
    W = layer.W.copy()
    if normalize_by_strength:
        s_out = W.sum(1)
        s_in = W.sum(0)
        denom = np.sqrt(np.outer(s_out, s_in))
        W = np.divide(W, denom, out=np.zeros_like(W), where=denom > 0)
    G = nx.DiGraph() if layer.directed else nx.Graph()
    G.add_nodes_from(layer.nodes)
    ii, jj = np.nonzero(W)
    for i, j in zip(ii, jj):
        if layer.directed or i < j:
            G.add_edge(layer.nodes[i], layer.nodes[j], distance=1.0 / W[i, j])
    bc = nx.betweenness_centrality(G, weight="distance", normalized=True)
    return pd.DataFrame({"iso3": list(bc), "betweenness": list(bc.values())})


def components(layer: Layer) -> dict[str, float]:
    G = layer.to_networkx()
    n = G.number_of_nodes()
    m = G.number_of_edges()
    possible = n * (n - 1) if layer.directed else n * (n - 1) / 2
    out = {"nodes": n, "edges": m, "density": m / possible if possible else np.nan}
    if layer.directed:
        out["weak_components"] = nx.number_weakly_connected_components(G)
        out["strong_components"] = nx.number_strongly_connected_components(G)
        out["largest_scc_share"] = max((len(c) for c in nx.strongly_connected_components(G)), default=0) / n if n else np.nan
    else:
        out["components"] = nx.number_connected_components(G)
        out["largest_cc_share"] = max((len(c) for c in nx.connected_components(G)), default=0) / n if n else np.nan
    w = layer.W[layer.W > 0]
    out.update({"weight_total": float(w.sum()) / (1 if layer.directed else 2),
                "weight_median": float(np.median(w)) if w.size else np.nan,
                "weight_p99": float(np.quantile(w, 0.99)) if w.size else np.nan})
    return out


def louvain(layer: Layer, seed: int, resolution: float = 1.0) -> dict[str, int]:
    G = layer.symmetrized().to_networkx()
    comms = nx.community.louvain_communities(G, weight="weight", resolution=resolution, seed=seed)
    return {n: k for k, c in enumerate(sorted(comms, key=lambda c: (-len(c), sorted(c)[0]))) for n in c}


def partition_agreement(p1: dict[str, int], p2: dict[str, int]) -> float:
    from sklearn.metrics import adjusted_mutual_info_score
    common = sorted(set(p1) & set(p2))
    return float(adjusted_mutual_info_score([p1[n] for n in common], [p2[n] for n in common]))


def country_profile(layer: Layer, partition: dict[str, str]) -> pd.DataFrame:
    """Per-country summary used in tables (normalized measures only)."""
    parts = [strengths(layer), concentration(layer, "out"), participation(layer, partition, "out")]
    if layer.directed:
        parts += [concentration(layer, "in"), participation(layer, partition, "in")]
    df = parts[0]
    for p in parts[1:]:
        df = df.merge(p, on="iso3")
    return df.assign(layer=layer.name)
