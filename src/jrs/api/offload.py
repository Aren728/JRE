"""Shared async-offload helper (Phase 6 Track B / Phase 7 Track C).

The evaluation pipeline (Swiss Ephemeris C extension, fact extraction,
yoga evaluation, evidence-graph construction) is synchronous CPU-bound
work. Running it inline inside ``async def`` endpoints blocks the event
loop and serializes all concurrent requests. :func:`offload` moves such
callables to the worker thread pool while preserving return-type
inference for mypy.
"""

from __future__ import annotations

import functools
import os
from typing import Any, Callable, TypeVar

import anyio

_R = TypeVar("_R")

#: Default ceiling for one blocking offload (seconds). Bounds the worst
#: case a hung/corrupted ephemeris call can hold a request. Set the env
#: var to "0" to disable (not recommended for production).
DEFAULT_OFFLOAD_TIMEOUT_SECONDS = 120.0


def _offload_timeout() -> float | None:
    raw = os.environ.get("JRS_OFFLOAD_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return DEFAULT_OFFLOAD_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_OFFLOAD_TIMEOUT_SECONDS
    return value if value > 0 else None


async def offload(func: Callable[..., _R], /, *args: Any, **kwargs: Any) -> _R:
    """Run a blocking, CPU-bound callable in the worker thread pool.

    Bounded by ``JRS_OFFLOAD_TIMEOUT_SECONDS`` (default 120s): on expiry
    :class:`TimeoutError` propagates so callers can map it to an HTTP
    504 instead of hanging. Note the worker thread itself keeps running
    to completion — the bound protects request latency, not the pool.
    """
    timeout = _offload_timeout()
    if timeout is None:
        return await anyio.to_thread.run_sync(functools.partial(func, *args, **kwargs))
    with anyio.fail_after(timeout):
        # abandon_on_cancel=True: on timeout the await returns immediately
        # (the worker thread runs to completion in the background) so the
        # request latency bound is actually enforced.
        return await anyio.to_thread.run_sync(
            functools.partial(func, *args, **kwargs),
            abandon_on_cancel=True,
        )
