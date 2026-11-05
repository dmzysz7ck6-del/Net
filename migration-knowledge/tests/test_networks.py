"""Directed/undirected semantics and null models (synthetic fixtures)."""
import numpy as np
import pandas as pd
import pytest

from src.networks.build import directed_layer, undirected_layer, canonical_pairs
from src.networks.nulls import ipf_directed, fitness_undirected, poisson_draw
from src.networks import metrics


def test_directed_orientation_origin_to_destination():
    df = pd.DataFrame({"origin": ["SOM", "SOM", "KEN"], "dest": ["KEN", "GBR", "GBR"], "stock": [100, 50, 7]})
    L = directed_layer(df, ["GBR", "KEN", "SOM"], "origin", "dest", "stock", "mig", "persons")
    i = L.index
    assert L.W[i["SOM"], i["KEN"]] == 100       # born in SOM, living in KEN
    assert L.W[i["KEN"], i["SOM"]] == 0         # not symmetric
    assert L.W.sum(1)[i["SOM"]] == 150          # out-strength = emigrants


def test_undirected_symmetric_and_rejects_double_listing():
    df = pd.DataFrame({"a": ["KEN", "ETH"], "b": ["USA", "KEN"], "n": [10, 3]})
    L = undirected_layer(df, ["ETH", "KEN", "USA"], "a", "b", "n", "col", "works")
    assert np.allclose(L.W, L.W.T)
    assert L.W[L.index["KEN"], L.index["ETH"]] == 3
    bad = pd.DataFrame({"a": ["KEN", "USA"], "b": ["USA", "KEN"], "n": [10, 10]})
    with pytest.raises(ValueError):
        undirected_layer(bad, ["KEN", "USA"], "a", "b", "n", "col", "works")
    can = canonical_pairs(bad, "a", "b")
    assert (can["a"] < can["b"]).all()


def test_self_loops_dropped():
    df = pd.DataFrame({"origin": ["KEN"], "dest": ["KEN"], "stock": [5]})
    L = directed_layer(df, ["KEN", "UGA"], "origin", "dest", "stock", "m", "p")
    assert L.W.sum() == 0


def test_ipf_preserves_margins_with_zero_diagonal():
    rng = np.random.default_rng(1)
    W = rng.gamma(1.0, 10.0, size=(8, 8)); np.fill_diagonal(W, 0)
    E = ipf_directed(W)
    assert np.allclose(E.sum(1), W.sum(1), rtol=1e-6)
    assert np.allclose(E.sum(0), W.sum(0), rtol=1e-6)
    assert np.allclose(np.diag(E), 0)


def test_fitness_preserves_strengths():
    rng = np.random.default_rng(2)
    A = rng.gamma(1.0, 5.0, size=(10, 10)); W = A + A.T; np.fill_diagonal(W, 0)
    E = fitness_undirected(W)
    assert np.allclose(E.sum(1), W.sum(1), rtol=1e-5)
    assert np.allclose(E, E.T)


def test_poisson_null_symmetric():
    rng = np.random.default_rng(3)
    E = np.full((5, 5), 4.0); np.fill_diagonal(E, 0)
    D = poisson_draw(E, False, rng)
    assert np.allclose(D, D.T) and np.allclose(np.diag(D), 0)


def test_disparity_filter_keeps_dominant_edge():
    nodes = list("ABCDE")
    W = np.ones((5, 5)); np.fill_diagonal(W, 0); W[0, 1] = W[1, 0] = 100
    from src.networks.build import Layer
    bb = metrics.disparity_backbone(Layer("t", nodes, W, False, ""), 0.05)
    assert bb.W[0, 1] == 100 and bb.W[2, 3] == 0


def test_participation_extra_regional():
    from src.networks.build import Layer
    nodes = ["A", "B", "C"]
    W = np.array([[0, 3, 1], [3, 0, 0], [1, 0, 0]], float)
    part = metrics.participation(Layer("t", nodes, W, False, ""), {"A": "x", "B": "x", "C": "y"}).set_index("iso3")
    assert part.loc["A", "extra_regional_share_out"] == pytest.approx(0.25)
    assert part.loc["A", "participation_out"] == pytest.approx(1 - (0.75 ** 2 + 0.25 ** 2))
