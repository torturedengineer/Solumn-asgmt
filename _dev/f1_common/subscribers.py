"""Synthetic subscriber directory. All data here is fake/generated."""
import random

_FIRST = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley",
    "Jamie", "Drew", "Sam", "Quinn", "Avery", "Reese",
]
_LAST = [
    "Chen", "Patel", "Garcia", "Kim", "Nguyen", "Smith",
    "Lopez", "Brown", "Diaz", "Khan", "Rossi", "Olsen",
]


def _make_subscriber(i: int) -> dict:
    rnd = random.Random(1000 + i)  # deterministic per index
    first = rnd.choice(_FIRST)
    last = rnd.choice(_LAST)
    email = f"{first.lower()}.{last.lower()}{i}@example.com"
    # Roughly a quarter of subscribers have opted in to delivery-confirmation
    # pings on a status-page callback. In practice, many different customers
    # happen to share the same handful of status-page SaaS providers, so it's
    # realistic that many of these point at the same host.
    has_callback = (i % 4 == 0)
    callback_url = "http://127.0.0.1:8765/confirm" if has_callback else None
    return {"id": i, "email": email, "active": True, "callback_url": callback_url}


def get_active_subscribers(n: int = 1200) -> list:
    """All current subscribers eligible for broadcast notifications."""
    return [_make_subscriber(i) for i in range(n)]


def get_digest_subscribers() -> list:
    """The small curated list used by the existing scheduled digest."""
    return get_active_subscribers(n=1200)[:40]
