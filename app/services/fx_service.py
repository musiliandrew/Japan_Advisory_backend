import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import settings


class FXService:
    def __init__(self) -> None:
        self._cached_rate: float | None = None
        self._cached_at: float = 0
        self._ttl_seconds = max(60, settings.fx_cache_ttl_seconds)

    def _fetch_from_exchange_rate_host(self) -> float:
        url = "https://api.exchangerate.host/convert?from=USD&to=KES"
        req = Request(url, headers={"User-Agent": "car-advisory-platform/1.0"})
        with urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = payload.get("result")
        if result is None:
            raise ValueError("Missing result from exchangerate.host")
        return float(result)

    def _fetch_from_open_er_api(self) -> float:
        url = "https://open.er-api.com/v6/latest/USD"
        req = Request(url, headers={"User-Agent": "car-advisory-platform/1.0"})
        with urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rates = payload.get("rates") or {}
        kes = rates.get("KES")
        if kes is None:
            raise ValueError("KES not present in open.er-api response")
        return float(kes)

    def _fetch_live_usd_to_kes(self) -> float:
        # Provider failover: if primary is down/limited, try secondary.
        try:
            return self._fetch_from_exchange_rate_host()
        except Exception:
            return self._fetch_from_open_er_api()

    def get_usd_to_kes(self) -> float:
        now = time.time()
        if self._cached_rate is not None and (now - self._cached_at) < self._ttl_seconds:
            return self._cached_rate

        try:
            rate = self._fetch_live_usd_to_kes()
            self._cached_rate = rate
            self._cached_at = now
            return rate
        except (URLError, ValueError, TimeoutError, OSError):
            # Last known-good rate if available; otherwise configured fallback.
            if self._cached_rate is not None:
                return self._cached_rate
            return settings.usd_to_kes_rate


fx_service = FXService()
