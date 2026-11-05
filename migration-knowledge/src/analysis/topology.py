"""Analysis E: do the layers have different hub, community and bridge structure?

All comparisons use a common node set and undirected versions of the
migration and mobility layers (W + W^T), because co-authorship is undirected.
Each observed statistic is benchmarked against strength-preserving Poisson
randomizations of the same layer (``networks.nulls``), so a country is only
called a bridge if it bridges *more than its total connectivity implies*.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..networks import metrics
from ..networks.build import Layer
from ..networks.nulls import expected, poisson_draw


def participation_z(layer: Layer, partition: dict[str, str], *, draws: int, seed: int) -> pd.DataFrame:
    """Participation coefficient (UN subregion partition) and its z-score under
    the strength-preserving null."""
    L = layer.symmetrized()
    obs = metrics.participation(L, partition, "out").set_index("iso3")
    E = expected(L.W, directed=False)
    rng = np.random.default_rng(seed)
    sims = []
    for _ in range(draws):
        D = poisson_draw(E, False, rng)
        sims.append(metrics.participation(Layer(L.name, L.nodes, D, False, L.unit), partition, "out")
                    .set_index("iso3")["participation_out"])
    S = pd.concat(sims, axis=1)
    mu, sd = S.mean(axis=1), S.std(axis=1, ddof=1)
    out = obs.rename(columns={"participation_out": "participation", "extra_regional_share_out": "extra_regional_share"})
    out["participation_null_mean"] = mu
    out["participation_z"] = (out["participation"] - mu) / sd.replace(0, np.nan)
    return out.reset_index().assign(layer=layer.name)


def backbone_betweenness(layer: Layer, alphas: list[float]) -> pd.DataFrame:
    L = layer.symmetrized()
    frames = []
    for a in alphas:
        bb = metrics.disparity_backbone(L, a)
        b = metrics.betweenness(bb).rename(columns={"betweenness": f"betweenness_a{a}"})
        frames.append(b.set_index("iso3"))
    return pd.concat(frames, axis=1).reset_index().assign(layer=layer.name)


def bridging_ranks(tables: dict[str, pd.DataFrame], cols: list[str]) -> pd.DataFrame:
    """Percentile rank of each bridging statistic within its layer."""
    out = []
    for name, t in tables.items():
        r = t[["iso3"]].copy()
        for c in cols:
            if c in t:
                r[f"rank_{c}"] = t[c].rank(pct=True)
        out.append(r.assign(layer=name))
    return pd.concat(out, ignore_index=True)


def community_agreement(layers: dict[str, Layer], *, seed: int, draws: int = 100) -> pd.DataFrame:
    """Adjusted mutual information between Louvain partitions of each pair of
    layers, versus the AMI between partitions of their null randomizations
    (what size structure alone would produce)."""
    names = list(layers)
    parts = {n: metrics.louvain(layers[n], seed=seed) for n in names}
    rng = np.random.default_rng(seed)
    exps = {n: expected(layers[n].symmetrized().W, False) for n in names}
    rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            obs = metrics.partition_agreement(parts[a], parts[b])
            null = []
            for d in range(draws):
                La = Layer(a, layers[a].nodes, poisson_draw(exps[a], False, rng), False, "")
                Lb = Layer(b, layers[b].nodes, poisson_draw(exps[b], False, rng), False, "")
                null.append(metrics.partition_agreement(metrics.louvain(La, seed=seed + d),
                                                        metrics.louvain(Lb, seed=seed + d)))
            rows.append({"layer_a": a, "layer_b": b, "ami": obs, "ami_null_mean": float(np.mean(null)),
                         "ami_null_p95": float(np.quantile(null, 0.95)),
                         "n_comm_a": len(set(parts[a].values())), "n_comm_b": len(set(parts[b].values()))})
    return pd.DataFrame(rows), parts


def layer_summary(layers: dict[str, Layer]) -> pd.DataFrame:
    return pd.DataFrame([{"layer": n, **metrics.components(L)} for n, L in layers.items()])
