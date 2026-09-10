"""Rate limiting and a spend cap for the LLM endpoint.

An LLM endpoint on a public URL with no limit on it is a free API you are
paying for on behalf of the internet. That is not a warning about a worst case.
It is what the thing is, from the moment you deploy it, and it takes one person
with a for-loop to find out.

This file is finished and works. What is not decided for you is the numbers:
REQUESTS_PER_MINUTE, DAILY_REQUEST_CAP and DAILY_TOKEN_CAP ship as placeholders
that are too small for anything real, and setting them is part of the
assignment. You cannot set them sensibly until you have measured tokens per
request, which is why MEASUREMENTS.md comes before this file in the order you
should work.

Two limits, because they stop different things:

    per caller     one bad client cannot starve everyone else
    global         everyone together cannot exceed what you can afford

A per-caller limit alone does not bound your bill. A thousand callers each
politely inside their limit still adds up to a thousand callers' worth of
tokens. The global cap is the one that actually protects you, and the
per-caller limit is the one that keeps the service usable while the global cap
is doing that.

Honest limitation, and say this in your README rather than hoping nobody asks:
these counters live in the memory of one process. They reset when the service
restarts, which on a free tier that sleeps after inactivity is often. They are
also per-replica, so two instances behind a load balancer enforce two separate
copies of every limit. The fix is a shared store, usually Redis, and it is out
of scope here. Knowing that your defence has that hole is the part an
interviewer is actually checking for.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Your numbers go here
# --------------------------------------------------------------------------
# These placeholders are deliberately tiny, so that if you deploy without
# thinking about them your service throttles instead of spending. Replace them
# with numbers you can defend out loud, derived from the table you fill in at
# the bottom of MEASUREMENTS.md.
#
# The question to answer for the global caps: what is the largest bill you are
# willing to wake up to? Divide that by your measured cost per request. That is
# DAILY_REQUEST_CAP. If the answer is "I am on a free tier and the bill cannot
# exceed zero," then the cap is your provider's published daily request limit
# minus the headroom you want for your own eval runs, and PROVIDERS.md has the
# numbers that were true when this template was written.

REQUESTS_PER_MINUTE = int(os.environ.get("LLM_REQUESTS_PER_MINUTE", "5"))
BURST = int(os.environ.get("LLM_BURST", "3"))
DAILY_REQUEST_CAP = int(os.environ.get("LLM_DAILY_REQUEST_CAP", "50"))
DAILY_TOKEN_CAP = int(os.environ.get("LLM_DAILY_TOKEN_CAP", "20000"))


class RateLimited(Exception):
    """This caller has asked too often. Their problem, and it clears on its own."""

    def __init__(self, message: str, retry_after: float) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class CapReached(Exception):
    """The whole service has spent its budget for the day. Everyone's problem.

    Separate from RateLimited on purpose. They deserve different status codes,
    different messages, and different reactions from you: a 429 is a client
    slowing down, and this is you finding out at 3pm that your day is over.
    """

    def __init__(self, message: str, resets_in: float) -> None:
        super().__init__(message)
        self.resets_in = resets_in


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class RateLimiter:
    """Token bucket per caller, plus a global daily request and token counter.

    A token bucket rather than a fixed window because a fixed window lets a
    caller send the whole minute's allowance in the last second of one window
    and again in the first second of the next, which is two minutes of traffic
    in two seconds and exactly the burst you were trying to prevent.

    "Token" here is the bucket kind, one per request. The `tokens` in
    DAILY_TOKEN_CAP is the model kind, thousands per request. Two different
    things sharing a word, which is unfortunate and is the industry's fault.
    """

    def __init__(
        self,
        requests_per_minute: int = REQUESTS_PER_MINUTE,
        burst: int = BURST,
        daily_request_cap: int = DAILY_REQUEST_CAP,
        daily_token_cap: int = DAILY_TOKEN_CAP,
    ) -> None:
        self.rate_per_second = requests_per_minute / 60.0
        self.burst = max(1, burst)
        self.daily_request_cap = daily_request_cap
        self.daily_token_cap = daily_token_cap

        self._buckets: dict[str, _Bucket] = {}
        self._day_started = time.monotonic()
        self._day_requests = 0
        self._day_model_tokens = 0
        # Uvicorn runs handlers in a thread pool, so two requests really can be
        # inside this object at once. Without the lock the global counter loses
        # increments under exactly the load that makes the cap matter.
        self._lock = threading.Lock()

    # -- global ------------------------------------------------------------

    def _roll_day_if_needed(self, now: float) -> None:
        if now - self._day_started >= 86400:
            self._day_started = now
            self._day_requests = 0
            self._day_model_tokens = 0

    def _seconds_until_reset(self, now: float) -> float:
        return max(0.0, 86400 - (now - self._day_started))

    # -- the check ---------------------------------------------------------

    def check(self, caller: str) -> None:
        """Allow this request, or raise. Call it before you spend anything.

        Order matters. The global cap is checked first, because when you are
        out of budget the answer is the same for every caller and there is no
        reason to make them wait behind a per-caller calculation.
        """
        now = time.monotonic()
        with self._lock:
            self._roll_day_if_needed(now)

            if self._day_requests >= self.daily_request_cap:
                raise CapReached(
                    f"Daily request cap of {self.daily_request_cap} reached.",
                    resets_in=self._seconds_until_reset(now),
                )
            if self._day_model_tokens >= self.daily_token_cap:
                raise CapReached(
                    f"Daily token cap of {self.daily_token_cap} reached.",
                    resets_in=self._seconds_until_reset(now),
                )

            bucket = self._buckets.get(caller)
            if bucket is None:
                bucket = _Bucket(tokens=float(self.burst), last_refill=now)
                self._buckets[caller] = bucket

            elapsed = now - bucket.last_refill
            bucket.tokens = min(self.burst, bucket.tokens + elapsed * self.rate_per_second)
            bucket.last_refill = now

            if bucket.tokens < 1.0:
                needed = (1.0 - bucket.tokens) / self.rate_per_second
                raise RateLimited(
                    f"Rate limit is {int(self.rate_per_second * 60)} requests per minute.",
                    retry_after=round(needed, 1),
                )

            bucket.tokens -= 1.0
            self._day_requests += 1

    def record_usage(self, model_tokens: int) -> None:
        """Add what a call actually cost, after it returns.

        Charged afterwards rather than reserved in advance, because you do not
        know the completion length until you have it. The consequence is that a
        single very long response can carry you past the token cap rather than
        being stopped at it, which is why max_tokens on the call is the other
        half of this defence. One request can overshoot. A thousand cannot.
        """
        with self._lock:
            self._day_model_tokens += max(0, model_tokens)

    def snapshot(self) -> dict:
        """Current usage, for /health and for your own screenshots.

        Publishing this is a small decision worth making deliberately. It tells
        an honest user why they are being throttled, and it tells a hostile one
        exactly how much of your budget is left. This template publishes it
        because the teaching value beats the risk at this scale. If your
        service has real users, reconsider.
        """
        now = time.monotonic()
        with self._lock:
            self._roll_day_if_needed(now)
            return {
                "requests_today": self._day_requests,
                "request_cap": self.daily_request_cap,
                "model_tokens_today": self._day_model_tokens,
                "token_cap": self.daily_token_cap,
                "requests_per_minute": int(self.rate_per_second * 60),
                "resets_in_seconds": int(self._seconds_until_reset(now)),
                "callers_tracked": len(self._buckets),
            }


limiter = RateLimiter()


def caller_id(request) -> str:
    """Who to charge this request to.

    Client IP, which is the weakest identifier there is: it is shared by
    everyone behind one NAT, it changes when a phone moves between towers, and
    anyone determined can get another one. It is used here because the seed has
    no accounts.

    If your app has authenticated users, key on the user id instead and delete
    this. If it does not, say in your README that your limit is per-IP and that
    you know what that does not cover. Naming the hole is worth more than
    pretending it is not there.

    X-Forwarded-For is read because every free host puts a proxy in front of
    you, and without it every request arrives from the proxy and shares one
    bucket. It is also trivially forgeable by the client, so trust it only as
    far as your host's documented behaviour, which usually means the last entry
    rather than the first.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    client = getattr(request, "client", None)
    return getattr(client, "host", None) or "unknown"
