"""Failed sign-ins per account and machine (phase 15).

The limit per IP (`login`) does not stop many machines trying passwords on one account, and a limit
per account alone would let anyone lock a known address out from a single machine. So each account
counts its failures per IP, with a higher total:

- `login_account` failures per account and IP: one machine can only pause itself on that account.
- ACCOUNT_TOTAL_FACTOR times that many in total, from any number of machines.
- Only failures count. A successful sign-in or a new password clears the account's count.
- Unknown addresses count the same as real ones, so the answer reveals nothing.
- The cache holds hashes: neither the address nor the IPs are stored in the cache table.
"""

import hashlib
import time

from django.core.cache import cache
from rest_framework.exceptions import Throttled
from rest_framework.settings import api_settings

SCOPE = "login_account"
PERIODS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
ACCOUNT_TOTAL_FACTOR = 5


def _limit() -> tuple[int, int]:
    """(failures, seconds) of the `login_account` rate, e.g. "10/hour" -> (10, 3600)."""
    number, period = api_settings.DEFAULT_THROTTLE_RATES[SCOPE].split("/")
    return int(number), PERIODS[period[0]]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _key(email: str) -> str:
    return f"login-attempts:{_hash(email.strip().lower())}"


def ensure_allowed(email: str, ip: str) -> None:
    """429 (`throttled`) while this machine, or all of them together, have used up their failures."""
    limit, _ = _limit()
    window = cache.get(_key(email))
    if window and (
        window["total"] >= limit * ACCOUNT_TOTAL_FACTOR
        or window["by_ip"].get(_hash(ip), 0) >= limit
    ):
        raise Throttled(wait=max(1, round(window["until"] - time.time())))


def record_failure(email: str, ip: str) -> None:
    _, period = _limit()
    now = time.time()
    window = cache.get(_key(email))
    if not window or window["until"] <= now:
        window = {"total": 0, "by_ip": {}, "until": now + period}
    window["total"] += 1
    machine = _hash(ip)
    window["by_ip"][machine] = window["by_ip"].get(machine, 0) + 1
    cache.set(_key(email), window, timeout=max(1, round(window["until"] - now)))


def clear(email: str) -> None:
    cache.delete(_key(email))
