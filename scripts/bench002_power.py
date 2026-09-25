#!/usr/bin/env python3
"""Phase 11A: JRE-BENCH-002 pre-registration power analysis.

Computes, deterministically and dependency-free, the statistical power
picture behind the JRE-BENCH-002 corpus expansion pre-registration
(``docs/validation/phase_11a_bench002_preregistration.md``):

1. the minimal number of discordant pairs m required for an exact
   two-sided McNemar test to reach significance at alpha when ALL
   discordant events point the same way (the best case the A3 ablation
   exhibited: b=0, c=m);
2. the power of the exact test for m discordant pairs under a
   per-pair regression probability of pi (sign-flip model: each
   discordant pair regresses w.p. pi, improves w.p. 1-pi);
3. the corpus expansion recommendation: given the discordant density
   observed on JRE-BENCH-001 (A3: 2 discordant pairs over 120 events),
   how many scored events are needed for the target power.

All probabilities are exact binomial sums — no approximations, no
third-party dependencies. The numbers printed here are the numbers
locked in the pre-registration document; the unit tests recompute them.

Usage::

    python scripts/bench002_power.py
    python scripts/bench002_power.py --json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

ALPHA = 0.05
TARGET_POWER = 0.80

# Observed on JRE-BENCH-001 (Phase 10 ablation, experiment A3):
# 2 discordant pairs (b=2, c=0) across 120 scored events.
OBSERVED_DISCORDANT = 2
OBSERVED_EVENTS = 120
OBSERVED_PI = 1.0  # both discordant events regressed (2/0 direction)

# Sign-flip models considered for the expansion (conservative -> optimistic).
PI_GRID: tuple[float, ...] = (0.80, 0.85, 0.90, 0.95, 1.0)


def min_discordant_for_significance(alpha: float = ALPHA) -> int:
    """Minimal all-one-direction discordant count reaching p <= alpha.

    Exact two-sided McNemar with b=0, c=m yields p = 2 * 0.5^m; solve
    2 * 0.5^m <= alpha.
    """
    m = 1
    while 2.0 * 0.5**m > alpha:
        m += 1
    return m


def exact_p_all_one_direction(m: int) -> float:
    """Exact two-sided McNemar p-value when b=0, c=m."""
    return min(1.0, 2.0 * 0.5**m)


def power_sign_flip(m: int, pi: float, alpha: float = ALPHA) -> float:
    """Power of the exact McNemar test with m discordant pairs under the
    sign-flip model P(regress) = pi per discordant pair.

    The test is significant iff the observed regressions b fall in the
    rejection region {b : p(b, m-b) <= alpha}; power is the exact
    binomial mass of that region under b ~ Bin(m, pi).
    """
    if not 0.0 <= pi <= 1.0:
        raise ValueError(f"pi must be in [0, 1], got {pi}")
    mass = 0.0
    for b in range(m + 1):
        p_value = mcnemar_p_exact(b, m - b)
        if p_value <= alpha:
            mass += math.comb(m, b) * pi**b * (1.0 - pi) ** (m - b)
    return mass


def mcnemar_p_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value (same convention as
    scripts/ablation_matrix.py): doubled binomial tail at the
    small-count side, clipped to 1."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) * 0.5**n
    return min(1.0, 2.0 * tail)


def events_needed(
    target_discordant: int,
    observed_discordant: int = OBSERVED_DISCORDANT,
    observed_events: int = OBSERVED_EVENTS,
) -> int:
    """Scored events needed to expect ``target_discordant`` pairs,
    scaling the observed discordant density linearly (rounded up to a
    whole multiple of the 40-chart / 3-events-per-chart corpus block)."""
    if observed_discordant <= 0:
        raise ValueError("observed discordant count must be positive")
    per_event = observed_discordant / observed_events
    raw = math.ceil(target_discordant / per_event)
    block = 120  # one 40-chart corpus block = 120 scored events
    return int(math.ceil(raw / block) * block)


def build_report() -> dict[str, Any]:
    m_min = min_discordant_for_significance()
    power_table = [
        {
            "discordant_pairs": m,
            "p_all_one_direction": exact_p_all_one_direction(m),
            **{
                f"power_pi_{str(pi).replace('.', '')}": round(
                    power_sign_flip(m, pi), 6
                )
                for pi in PI_GRID
            },
        }
        for m in (4, 5, 6, 7, 8, 9, 10, 12, 16, 20)
    ]
    # Minimal m reaching TARGET_POWER under each pi model.
    m_needed = {}
    for pi in PI_GRID:
        m = m_min
        while power_sign_flip(m, pi) < TARGET_POWER:
            m += 1
            if m > 200:  # safety bound
                break
        m_needed[f"pi_{pi}"] = m
    target_m = m_needed["pi_0.9"]
    return {
        "schema_version": "1.0.0",
        "analysis_id": "JRE-BENCH-002-POWER",
        "alpha": ALPHA,
        "target_power": TARGET_POWER,
        "min_discordant_for_significance": m_min,
        "p_at_min": exact_p_all_one_direction(m_min),
        "power_table": power_table,
        "m_needed_by_pi": m_needed,
        "recommendation": {
            "target_discordant_pairs": target_m,
            "target_pi": 0.9,
            "power_at_target": round(power_sign_flip(target_m, 0.9), 6),
            "scored_events_needed": events_needed(target_m),
            "charts_needed": events_needed(target_m) // 3,
            "observed_density_basis": (
                f"{OBSERVED_DISCORDANT} discordant pairs / "
                f"{OBSERVED_EVENTS} scored events (A3, JRE-BENCH-001)"
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="JRE-BENCH-002 pre-registration power analysis."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("JRE-BENCH-002 PRE-REGISTRATION POWER ANALYSIS")
    print(
        f"alpha={report['alpha']} | target power={report['target_power']} | "
        f"min discordant pairs for significance (one-directional): "
        f"{report['min_discordant_for_significance']} "
        f"(p={report['p_at_min']})"
    )
    print()
    header = (
        f"{'m':>3} {'p(b=0)':>10} "
        + " ".join(f"{'pi=' + str(pi):>9}" for pi in PI_GRID)
    )
    print(header)
    print("-" * len(header))
    for row in report["power_table"]:
        cells = " ".join(
            f"{row[f'power_pi_{str(pi).replace('.', '')}']:>9.4f}" for pi in PI_GRID
        )
        print(f"{row['discordant_pairs']:>3} {row['p_all_one_direction']:>10.5f} {cells}")
    rec = report["recommendation"]
    print()
    print(
        f"recommendation: >= {rec['scored_events_needed']} scored events "
        f"({rec['charts_needed']} charts) -> ~{rec['target_discordant_pairs']} "
        f"discordant pairs at the observed density; power = "
        f"{rec['power_at_target']} under pi=0.9"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
