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
from typing import Any, Callable, TypeVar

import anyio

_R = TypeVar("_R")


async def offload(func: Callable[..., _R], /, *args: Any, **kwargs: Any) -> _R:
    """Run a blocking, CPU-bound callable in the worker thread pool."""
    return await anyio.to_thread.run_sync(functools.partial(func, *args, **kwargs))
