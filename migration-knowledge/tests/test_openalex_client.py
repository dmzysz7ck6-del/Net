"""OpenAlex client behaviour against a fake HTTP session (no network)."""
import json

import pytest

from src.acquisition import openalex as OA
from src.http import CachedClient, PaymentRequired


class FakeResp:
    def __init__(self, status, payload):
        self.status_code, self._p, self.headers, self.text = status, payload, {}, json.dumps(payload)

    def json(self):
        return self._p

    def raise_for_status(self):
        raise RuntimeError(self.status_code)


class FakeSession:
    def __init__(self, router):
        self.router, self.headers, self.calls = router, {}, []

    def get(self, url, params=None, timeout=None, stream=False):
        self.calls.append(dict(params or {}))
        return self.router(params or {})


def client_with(router, tmp_path):
    oa = OA.OpenAlex.__new__(OA.OpenAlex)
    oa.cfg = {"per_page": 200, "work_filters": {"type": "article"}}
    oa.base, oa.mailto, oa.api_key = "https://api.example.org", None, "SECRET"
    oa.client = CachedClient(tmp_path, requests_per_second=0, session=FakeSession(router))
    return oa


def test_group_by_paginates_and_parses_unknown(tmp_path):
    def router(p):
        if p.get("group_by") == "countries_distinct_count":
            return FakeResp(200, {"meta": {"groups_count": 3, "next_cursor": None},
                                  "group_by": [{"key": "1", "count": 10}, {"key": "2", "count": 4}, {"key": "unknown", "count": 7}]})
        if p.get("cursor") == "*":
            return FakeResp(200, {"meta": {"groups_count": 3, "next_cursor": "c2"},
                                  "group_by": [{"key": "https://openalex.org/countries/KE", "count": 4},
                                               {"key": "https://openalex.org/countries/US", "count": 3}]})
        return FakeResp(200, {"meta": {"groups_count": 3, "next_cursor": None},
                              "group_by": [{"key": "https://openalex.org/countries/GB", "count": 1}]})
    oa = client_with(router, tmp_path)
    t = oa.country_k_table("KE", (2015, 2019))
    assert set(t["partner"]) == {"KE", "US", "GB"} and (t["k"] == 2).all()
    assert t["sum_check"].iloc[0] == pytest.approx((4 + 3 + 1) / (2 * 4))
    # secrets never reach the cache files
    assert all("SECRET" not in p.read_text() for p in tmp_path.rglob("*.json"))


def test_truncated_groups_raise(tmp_path):
    oa = client_with(lambda p: FakeResp(200, {"meta": {"groups_count": 300, "next_cursor": None},
                                              "group_by": [{"key": "US", "count": 1}]}), tmp_path)
    with pytest.raises(RuntimeError, match="groups_count"):
        oa.group_by({"x": "y"}, "authorships.countries")


def test_payment_required_stops(tmp_path):
    oa = client_with(lambda p: FakeResp(402, {"error": "pay"}), tmp_path)
    with pytest.raises(PaymentRequired):
        oa.count({"x": "y"})


def test_cache_makes_reruns_free(tmp_path):
    def router(p):
        return FakeResp(200, {"meta": {"count": 5}, "results": []})
    oa = client_with(router, tmp_path)
    assert oa.count({"a": "b"}) == 5 and oa.count({"a": "b"}) == 5
    assert len(oa.client.session.calls) == 1
