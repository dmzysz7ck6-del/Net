"""HTTP utilities: persistent caching, request logging, rate limiting and
exponential backoff.

Every JSON API response is cached on disk under a key derived from the URL and
the (non-secret) query parameters, so re-running the pipeline is incremental
and resumable: a killed run picks up from the last cached request. Secrets
(API keys) are taken from environment variables, are never written to the
cache key, the cache file or the request log.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Iterable

import requests

from .provenance import utcnow

SECRET_PARAMS = {"api_key", "apikey", "key", "token", "access_token", "mailto"}


class AccessDenied(RuntimeError):
    """Raised when a host is blocked by policy (HTTP 403 at the proxy/CONNECT)."""


class PaymentRequired(RuntimeError):
    """HTTP 402: the API wants payment. The pipeline must stay zero-cost, so it
    stops immediately instead of retrying."""


def _public(params: dict[str, Any] | None) -> dict[str, Any]:
    return {k: v for k, v in sorted((params or {}).items()) if k.lower() not in SECRET_PARAMS}


def redact(text: str, secrets: dict[str, Any] | None) -> str:
    """Remove secret values (and their URL-encoded forms) from a message."""
    from urllib.parse import quote, quote_plus
    out = str(text)
    for v in (secrets or {}).values():
        if v:
            for form in {str(v), quote(str(v), safe=""), quote_plus(str(v))}:
                out = out.replace(form, "***")
    return out


def cache_key(url: str, params: dict[str, Any] | None) -> str:
    blob = json.dumps({"url": url, "params": _public(params)}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:32]


class CachedClient:
    """A small, polite JSON/binary HTTP client."""

    def __init__(self, cache_dir: Path, log_path: Path | None = None, *,
                 requests_per_second: float = 5.0, max_retries: int = 8,
                 backoff_base: float = 1.5, timeout: float = 120.0,
                 user_agent: str = "migration-knowledge-research/0.1 (+reproducible research pipeline)",
                 session: requests.Session | None = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = Path(log_path) if log_path else self.cache_dir / "requests.jsonl"
        self.min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0.0
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._last = 0.0
        self.stats = {"cache_hits": 0, "requests": 0, "retries": 0}

    # -- internals ---------------------------------------------------------
    def _throttle(self) -> None:
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def _log(self, **entry: Any) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": utcnow(), **entry}, sort_keys=True) + "\n")

    def _request(self, url: str, params: dict[str, Any] | None, stream: bool = False) -> requests.Response:
        secrets = {k: v for k, v in (params or {}).items() if k.lower() in SECRET_PARAMS}
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout, stream=stream)
            except requests.exceptions.ProxyError as exc:  # CONNECT refused by policy
                if "403" in str(exc):
                    # 'from None': the chained ProxyError text could contain secret query values
                    raise AccessDenied(f"host blocked by network policy: {url}") from None
                last_exc = exc
            except requests.exceptions.RequestException as exc:
                last_exc = exc
            else:
                self.stats["requests"] += 1
                if resp.status_code == 200:
                    return resp
                if resp.status_code == 402:
                    self._log(url=url, params=_public(params), status=402, body=resp.text[:500])
                    raise PaymentRequired(f"{url} returned 402 Payment Required; stopping (zero-cost policy)")
                if resp.status_code in (429, 500, 502, 503, 504):
                    retry_after = resp.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else self.backoff_base ** (attempt + 1)
                    self._log(url=url, params=_public(params), status=resp.status_code, retry_in=delay)
                    self.stats["retries"] += 1
                    time.sleep(min(delay, 300))
                    continue
                self._log(url=url, params=_public(params), status=resp.status_code, body=redact(resp.text[:500], secrets))
                raise requests.HTTPError(redact(f"HTTP {resp.status_code} for {url}", secrets))
            delay = self.backoff_base ** (attempt + 1)
            self.stats["retries"] += 1
            self._log(url=url, params=_public(params), error=redact(repr(last_exc), secrets), retry_in=delay)
            time.sleep(min(delay, 300))
        raise RuntimeError(redact(f"giving up on {url} after {self.max_retries} retries: {last_exc!r}", secrets))

    # -- public API ----------------------------------------------------------
    def get_json(self, url: str, params: dict[str, Any] | None = None, *,
                 secret_params: dict[str, Any] | None = None, refresh: bool = False) -> dict[str, Any]:
        """GET a JSON document, served from cache when available."""
        key = cache_key(url, params)
        path = self.cache_dir / key[:2] / f"{key}.json"
        if path.exists() and not refresh:
            self.stats["cache_hits"] += 1
            return json.loads(path.read_text(encoding="utf-8"))["response"]
        full = dict(params or {})
        full.update(secret_params or {})
        t0 = time.monotonic()
        resp = self._request(url, full)
        data = resp.json()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"url": url, "params": _public(params), "retrieved_utc": utcnow(),
                                   "response": data}), encoding="utf-8")
        tmp.replace(path)  # atomic: a crash never leaves a half-written cache entry
        self._log(url=url, params=_public(params), status=200, seconds=round(time.monotonic() - t0, 3), cache=str(path.name))
        return data

    def download(self, url: str, dest: Path, *, refresh: bool = False, chunk: int = 1 << 20) -> Path:
        """Stream a file to ``dest`` (resumable at file granularity)."""
        dest = Path(dest)
        if dest.exists() and dest.stat().st_size > 0 and not refresh:
            self.stats["cache_hits"] += 1
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = self._request(url, None, stream=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as fh:
            for block in resp.iter_content(chunk_size=chunk):
                fh.write(block)
        tmp.replace(dest)
        self._log(url=url, status=200, file=str(dest.name), bytes=dest.stat().st_size)
        return dest


def check_hosts(urls: Iterable[str], timeout: float = 20.0) -> dict[str, str]:
    """Return a status string per URL: 'ok', 'blocked (403 at proxy)', or the error."""
    out: dict[str, str] = {}
    for url in urls:
        try:
            r = requests.get(url, timeout=timeout)
            out[url] = "ok" if r.status_code < 400 else f"http {r.status_code}"
        except requests.exceptions.ProxyError as exc:
            out[url] = "blocked (403 at proxy)" if "403" in str(exc) else f"proxy error: {exc}"
        except requests.exceptions.RequestException as exc:
            out[url] = f"error: {type(exc).__name__}"
    return out
