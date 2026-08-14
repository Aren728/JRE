"""Deterministic repeated calculations (req. K, test plan §16)."""

from __future__ import annotations

from pathlib import Path

from tests.integration.jyotish.conftest import make_birth

from jyotish.models import JyotishConfig

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_same_query_twice_bit_identical(service):
    import datetime as dt

    def states():
        return service.planetary_state(
            dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.209
        )

    assert [s.to_dict() for s in states()] == [s.to_dict() for s in states()]


def test_chart_deterministic(service):
    chart_a = service.chart(make_birth()).to_dict()
    chart_b = service.chart(make_birth()).to_dict()
    assert chart_a == chart_b


def test_config_changes_are_isolated(service):
    """Interleaving configs must not leak state into later calls."""
    import datetime as dt

    from jyotish.models import ZodiacMode

    sid = service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.209
    )
    service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.209,
        config=JyotishConfig(zodiac_mode=ZodiacMode.TROPICAL, ayanamsa=None),
    )
    sid_again = service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.209
    )
    assert [s.to_dict() for s in sid] == [s.to_dict() for s in sid_again]


def test_transit_events_deterministic_across_process_boundaries():
    """Cross-process determinism: identical queries in two fresh processes."""
    import subprocess
    import sys
    import textwrap

    code = textwrap.dedent(
        """
        import datetime as dt
        from jyotish.service import JyotishService
        from astronomy.models import BodyId
        from jyotish.models import TransitEventKind

        svc = JyotishService()
        events = svc.events_between(
            "2001-01-01T00:00:00Z", "2001-03-01T00:00:00Z",
            (BodyId.SUN, BodyId.MOON),
            (TransitEventKind.RASHI_INGRESS,),
        )
        print([round(e.event_julian_day_ut, 9) for e in events])
        """
    )
    run_args = [sys.executable, "-c", code]
    out1 = subprocess.run(
        run_args, capture_output=True, text=True, cwd=REPO_ROOT
    )
    out2 = subprocess.run(
        run_args, capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert out1.returncode == 0, out1.stderr
    assert out2.returncode == 0, out2.stderr
    assert out1.stdout == out2.stdout
