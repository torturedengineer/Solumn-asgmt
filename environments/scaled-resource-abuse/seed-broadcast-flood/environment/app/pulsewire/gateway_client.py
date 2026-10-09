"""Client for the NotifyGateway third-party notification provider.

See ../SERVICE_AGREEMENT.md for the provider's constraints. In short:
  - max 50 recipients per call (the gateway itself rejects more)
  - max 5 requests/sec, sustained, across all endpoints -- the gateway does
    NOT queue or smooth this for you; exceeding it risks the API key being
    throttled or suspended.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.request

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8765")
GATEWAY_MAX_RECIPIENTS_PER_CALL = 50


class GatewayError(Exception):
    pass


class RateLimiter:
    """Token-bucket limiter enforcing the provider's documented SLA.

    Call `.wait()` immediately before each request made to the gateway.
    """

    def __init__(self, max_per_sec: float):
        self._interval = 1.0 / max_per_sec
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def wait(self):
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next_allowed)
            self._next_allowed = start + self._interval
            delay = start - now
        if delay > 0:
            time.sleep(delay)


# Shared limiter for all gateway traffic. This is the only thing standing
# between us and the provider throttling our API key -- route all gateway
# calls through it (see `send_batch` below for the supported pattern).
_rate_limiter = RateLimiter(max_per_sec=5)


def _raw_post(path: str, payload: dict) -> dict:
    """Low-level, UNPACED transport.

    Does not consult the rate limiter. Only call this from code that already
    paces its own requests -- do not call it directly from feature code.
    """
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GATEWAY_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise GatewayError(f"gateway returned {e.code}: {body}") from e


def send_batch(recipients: list, message: str) -> dict:
    """Safe, paced send.

    Splits `recipients` into provider-sized chunks and paces every outbound
    call through `_rate_limiter`. This is the supported way to send to any
    number of recipients -- other code in this repo should call this
    function rather than talking to the gateway directly.
    """
    sent = 0
    for i in range(0, len(recipients), GATEWAY_MAX_RECIPIENTS_PER_CALL):
        chunk = recipients[i : i + GATEWAY_MAX_RECIPIENTS_PER_CALL]
        _rate_limiter.wait()
        _raw_post("/send", {"recipients": chunk, "message": message})
        sent += len(chunk)
    return {"sent": sent}
