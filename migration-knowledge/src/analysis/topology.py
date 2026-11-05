"""Analysis E: do the layers have different hub, community and bridge structure?

All comparisons use a common node set and undirected versions of the
migration and mobility layers (W + W^T), because co-authorship is undirected.
Each observed statistic is benchmarked against strength-preserving NB2
randomizations of the same layer, with the layer's own estimated dispersion
(``networks.nulls``), so a country is only called a bridge if it bridges *more
than its total connectivity implies*, and the comparison does not depend on
the layer's unit of measurement.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..networks import metrics
from ..networks.build import Layer
from ..networks.nulls import expected, layer_alpha, nb_draw, poisson_draw


def _null_draws(layer: Layer, alpha: float | None, draws: int, seed: int, full: Layer | None = None):
    """NB2 null networks. For a fractional layer pass ``full`` (the full-count
    layer): draws are made in whole papers around the full layer's expectation
    with its dispersion, then converted with each pair's observed frac/full
    ratio, so no NB draw is ever made around a fractional mean."""
    L = layer.symmetrized()
    rng = np.random.default_rng(seed)
    if full is None:
        E = expected(L.W, directed=False)
        a = alpha if alpha is not None else layer_alpha(L.W, E, False)
        return L, E, a, (Layer(L.name, L.nodes, nb_draw(E, a, False, rng), False, L.unit) for _ in range(draws))
    F = full.symmetrized()
    Ef = expected(F.W, directed=False)
    a = alpha if alpha is not None else layer_alpha(F.W, Ef, False)
    glob = L.W.sum() / F.W.sum() if F.W.sum() > 0 else 1.0
    ratio = np.where(F.W > 0, np.divide(L.W, F.W, out=np.zeros_like(L.W), where=F.W > 0), glob)
    return L, Ef, a, (Layer(L.name, L.nodes, nb_draw(Ef, a, False, rng) * ratio, False, L.unit) for _ in range(draws))


def participation_z(layer: Layer, partition: dict[str, str], *, draws: int, seed: int,
                    alpha: float | None = None, full: Layer | None = None) -> pd.DataFrame:
    """Participation coefficient (UN subregion partition) versus an NB2
    strength-preserving null with the layer's own dispersion.

    Primary (unit-free): ``participation_dev = P_obs - mean(P_null)``. A Poisson
    null would make z-scores scale with the layer's unit (persons vs papers),
    so the null uses NB2 noise whose relative size is estimated from the layer."""
    L, E, a, sims_iter = _null_draws(layer, alpha, draws, seed, full)
    obs = metrics.participation(L, partition, "out").set_index("iso3")
    sims = [metrics.participation(D, partition, "out").set_index("iso3")["participation_out"] for D in sims_iter]
    S = pd.concat(sims, axis=1)
    mu, sd = S.mean(axis=1), S.std(axis=1, ddof=1)
    out = obs.rename(columns={"participation_out": "participation", "extra_regional_share_out": "extra_regional_share"})
    out["participation_null_mean"] = mu
    out["participation_dev"] = out["participation"] - mu
    out["participation_z"] = (out["participation"] - mu) / sd.replace(0, np.nan)
    out["null_alpha"] = a
    return out.reset_index().assign(layer=layer.name)


def backbone_betweenness(layer: Layer, alphas: list[float], *, null_draws: int = 0, seed: int = 0,
                         alpha: float | None = None, full: Layer | None = None) -> pd.DataFrame:
    """Betweenness on disparity backbones, with a null-calibrated score per
    country: the mid-rank percentile of the observed value within its
    betweenness on NB2 strength-preserving null networks
    (P(null < obs) + 0.5 P(null = obs)). Raw betweenness on backbones is
    strongly size-related, so only the calibrated score is compared across
    layers."""
    L = layer.symmetrized()
    frames = []
    for a in alphas:
        bb = metrics.disparity_backbone(L, a)
        b = metrics.betweenness(bb).rename(columns={"betweenness": f"betweenness_a{a}"}).set_index("iso3")
        frames.append(b)
    out = pd.concat(frames, axis=1)
    if null_draws:
        _, _, na, sims_iter = _null_draws(layer, alpha, null_draws, seed, full)
        sims = {a: [] for a in alphas}
        for D in sims_iter:
            for a in alphas:
                sims[a].append(metrics.betweenness(metrics.disparity_backbone(D, a)).set_index("iso3")["betweenness"])
        for a in alphas:
            S = pd.concat(sims[a], axis=1).reindex(out.index)
            o = out[f"betweenness_a{a}"]
            less = S.lt(o, axis=0).mean(axis=1)
            eq = S.eq(o, axis=0).mean(axis=1)
            out[f"betweenness_calib_a{a}"] = less + 0.5 * eq
        out["null_alpha"] = na
    return out.reset_index().assign(layer=layer.name)


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


def community_agreement(layers: dict[str, Layer], *, seed: int, draws: int = 100,
                        alphas: dict[str, float] | None = None) -> pd.DataFrame:
    """Adjusted mutual information between Louvain partitions of each pair of
    layers, versus the AMI between partitions of NB2 null draws (what size
    structure alone produces). Null draws whose partition is a single community
    are excluded (sklearn scores two single-community partitions as AMI = 1),
    and their count is reported."""
    names = list(layers)
    parts = {n: metrics.louvain(layers[n], seed=seed) for n in names}
    rng = np.random.default_rng(seed)
    exps = {n: expected(layers[n].symmetrized().W, False) for n in names}
    alph = {n: (alphas or {}).get(n) or layer_alpha(layers[n].symmetrized().W, exps[n], False) for n in names}
    rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            obs = metrics.partition_agreement(parts[a], parts[b])
            null, degenerate = [], 0
            for d in range(draws):
                La = Layer(a, layers[a].nodes, nb_draw(exps[a], alph[a], False, rng), False, "")
                Lb = Layer(b, layers[b].nodes, nb_draw(exps[b], alph[b], False, rng), False, "")
                pa, pb = metrics.louvain(La, seed=seed + d), metrics.louvain(Lb, seed=seed + d)
                if len(set(pa.values())) < 2 or len(set(pb.values())) < 2:
                    degenerate += 1
                    continue
                null.append(metrics.partition_agreement(pa, pb))
            rows.append({"layer_a": a, "layer_b": b, "ami": obs,
                         "ami_null_mean": float(np.mean(null)) if null else np.nan,
                         "ami_null_p95": float(np.quantile(null, 0.95)) if null else np.nan,
                         "null_draws_used": len(null), "null_draws_single_community": degenerate,
                         "n_comm_a": len(set(parts[a].values())), "n_comm_b": len(set(parts[b].values()))})
    return pd.DataFrame(rows), parts


def layer_summary(layers: dict[str, Layer]) -> pd.DataFrame:
    return pd.DataFrame([{"layer": n, **metrics.components(L)} for n, L in layers.items()])
