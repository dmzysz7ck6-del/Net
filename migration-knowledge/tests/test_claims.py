"""Claim tokens resolve to generated outputs and are verified."""
import json

import pytest

from src.config import PATHS
from src.reporting import claims


@pytest.fixture
def root(tmp_path):
    old = PATHS.root
    PATHS.set_root(tmp_path); PATHS.ensure()
    (PATHS.models / "summary_primary.json").write_text(json.dumps({"alignment": {"h1": {"median_rho_resid": 0.4123}}}))
    yield tmp_path
    PATHS.set_root(old)


def test_render_and_verify(root):
    t = root / "t.md"
    t.write_text("Median rho was {{summary_primary.alignment.h1.median_rho_resid:.2f}}.")
    out = claims.render(t, root / "outputs" / "findings.md")
    assert out.read_text() == "Median rho was 0.41."
    assert claims.verify([out]) == []
    (PATHS.models / "summary_primary.json").unlink()
    assert claims.verify([out])  # source removed -> flagged


def test_unknown_claim_raises(root):
    t = root / "t.md"
    t.write_text("{{nope.value}}")
    with pytest.raises(KeyError):
        claims.render(t, root / "x.md")
