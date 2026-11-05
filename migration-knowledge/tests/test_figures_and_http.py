"""Small invariants: diverging colour direction matches the Figure 2 key;
secrets are redacted from log/exception text."""
from src.http import redact
from src.visualization import style as S


def test_diverging_direction_matches_caption():
    # Figure 2 plots (collaboration share - migrant share): positive -> red
    hi, lo = S.DIVERGING(1.0), S.DIVERGING(0.0)
    assert hi[0] > hi[2] and lo[2] > lo[0]
    import inspect
    from src.visualization import figures as F
    src = inspect.getsource(F.figure2_divergence)
    assert "Red: the destination's share of the origin's co-authored articles exceeds" in src
    assert "(q - p) * 100" in inspect.getsource(F.divergence_matrix)


def test_redact_secret_values():
    msg = "ConnectionError: https://api.example.org/works?filter=x&api_key=S3CR3T%2B1&mailto=a%40b.org"
    out = redact(msg, {"api_key": "S3CR3T+1", "mailto": "a@b.org"})
    assert "S3CR3T" not in out and "a%40b.org" not in out and "***" in out
