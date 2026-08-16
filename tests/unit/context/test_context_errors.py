"""Error taxonomy tests (SPEC §7, DC §3)."""

from __future__ import annotations

import pytest

from context import (
    ContextComputationError,
    ContextError,
    InvalidContextConfigError,
    InvalidContextRequestError,
)


def test_error_hierarchy() -> None:
    assert issubclass(InvalidContextConfigError, ContextError)
    assert issubclass(InvalidContextRequestError, ContextError)
    assert issubclass(ContextComputationError, ContextError)


def test_message_preserved() -> None:
    err = InvalidContextConfigError("bad config")
    assert str(err) == "bad config"
    err2 = InvalidContextRequestError("bad request")
    assert str(err2) == "bad request"
    err3 = ContextComputationError("delegated chart failed")
    assert str(err3) == "delegated chart failed"


def test_no_raw_valueerror_escapes_surface(fake_jyotish, fake_bhava) -> None:
    """Config/request validation paths raise only the typed errors."""
    from context import ContextConfig

    with pytest.raises(ContextError):
        ContextConfig(house_system="BOGUS")
    with pytest.raises(ContextError):
        ContextConfig(default_time_precision="NOPE")
