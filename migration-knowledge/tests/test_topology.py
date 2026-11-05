"""Topology statistics: unit invariance of the NB2 null and the bridge rule."""
import numpy as np

from src.analysis import topology as T
from src.networks.build import Layer


def gravity_layer(n=25, scale=1.0, seed=0):
    rng = np.random.default_rng(seed)
    nodes = [f"C{i:02d}" for i in range(n)]
    size = rng.lognormal(0, 1, n)
    xy = rng.uniform(0, 10, (n, 2))
    D = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1)) + 1
    W = rng.poisson(20 * np.outer(size, size) / D * np.exp(rng.normal(0, 0.5, (n, n))))
    W = np.triu(W, 1); W = (W + W.T).astype(float) * scale
    part = {nd: ("A" if xy[i, 0] < 5 else "B") for i, nd in enumerate(nodes)}
    return Layer("t", nodes, W, False, ""), part


def test_participation_deviation_is_unit_free():
    L1, part = gravity_layer(scale=1.0)
    L2 = Layer("t", L1.nodes, L1.W * 1000, False, "")
    a = T.participation_z(L1, part, draws=40, seed=1)
    b = T.participation_z(L2, part, draws=40, seed=1)
    # identical observed P; NB2 relative dispersion makes the null comparable across units
    assert np.allclose(a["participation"], b["participation"])
    assert np.corrcoef(a["participation_dev"], b["participation_dev"])[0, 1] > 0.9
    assert abs(a["participation_z"].abs().median() - b["participation_z"].abs().median()) < 2.0


def test_calibrated_betweenness_in_unit_interval():
    L, _ = gravity_layer()
    bb = T.backbone_betweenness(L, [0.05], null_draws=10, seed=2)
    c = bb["betweenness_calib_a0.05"]
    assert c.between(0, 1).all()
