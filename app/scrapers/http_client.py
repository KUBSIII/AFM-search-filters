from collections.abc import Callable
import time

import httpx

from app.scrapers.exceptions import TransfermarktRequestError, TransfermarktResponseError

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class TransfermarktHttpClient:
    def __init__(
        self,
        timeout_s: float,
        max_retries: int,
        backoff_base_s: float,
        rate_limit_rps: float,
        client: httpx.Client | None = None,
        sleep_func: Callable[[float], None] | None = None,
    ):
        self.timeout_s = timeout_s
        self.max_retries = max(0, max_retries)
        self.backoff_base_s = max(0.0, backoff_base_s)
        self.rate_limit_rps = max(0.1, rate_limit_rps)
        self._client = client or httpx.Client(timeout=timeout_s, follow_redirects=True)
        self._sleep = sleep_func or time.sleep
        self._next_allowed_at = 0.0

    def close(self) -> None:
        self._client.close()

    def get_text(self, url: str) -> str:
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            self._wait_for_rate_limit()

            try:
                response = self._client.get(url, headers={"User-Agent": "AFM-search-filters/0.1"})
            except httpx.RequestError as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                self._sleep(self.backoff_base_s * (2**attempt))
                continue

            if response.status_code in RETRY_STATUS_CODES and attempt < self.max_retries:
                self._sleep(self.backoff_base_s * (2**attempt))
                continue

            if response.status_code >= 400:
                raise TransfermarktResponseError(
                    f"Transfermarkt returned status {response.status_code} for {url}"
                )

            return response.text

        raise TransfermarktRequestError(f"Request failed for {url}: {last_error}")

    def _wait_for_rate_limit(self) -> None:
        interval = 1.0 / self.rate_limit_rps
        now = time.monotonic()
        if now < self._next_allowed_at:
            self._sleep(self._next_allowed_at - now)
        self._next_allowed_at = max(now, self._next_allowed_at) + interval
