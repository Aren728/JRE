"""
tests/load/locustfile.py

High-concurrency Locust load test suite for JRE/JRS v1.0.0 API.
Targets: POST /api/v1/events/evaluate

Usage:
    locust -f tests/load/locustfile.py --host http://localhost:8080
"""

from __future__ import annotations

import random
from typing import Any, Dict

from locust import FastHttpUser, events, task, between


# --- Test Data Pools for Dynamic Payload Generation ---

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]
DASHA_LORDS = [
    "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
]
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def generate_mock_chart() -> Dict[str, Any]:
    """Generates a randomized synthetic chart payload for Tier 1 evaluation."""
    selected_planets = random.sample(PLANETS, k=random.randint(5, 9))
    chart_planets: Dict[str, Any] = {}

    for idx, planet in enumerate(selected_planets):
        chart_planets[planet] = {
            "house": (idx % 12) + 1,
            "sign": random.choice(SIGNS),
            "degree": round(random.uniform(0.0, 29.99), 2),
        }

    return {"planets": chart_planets}


def generate_event_context() -> Dict[str, Any]:
    """Generates randomized Dasha context parameters for Tier 2 filtering."""
    dasha, bhukti = random.sample(DASHA_LORDS, k=2)
    pratyantar = random.choice(DASHA_LORDS)

    year = random.randint(2020, 2030)
    month = random.randint(1, 12)
    day = random.randint(1, 28)

    return {
        "event_date": f"{year:04d}-{month:02d}-{day:02d}",
        "dasha_lord": dasha,
        "bhukti_lord": bhukti,
        "pratyantardasha_lord": pratyantar,
    }


# --- Locust Test User Definition ---


class EventEvaluatorLoadTestUser(FastHttpUser):
    """
    High-performance user class utilizing gevent/cHTTPClient for
    maximum concurrency throughput with low CPU overhead.
    """

    # Simulates user think time between requests (0.01s - 0.05s for aggressive
    # stress testing)
    wait_time = between(0.01, 0.05)

    @task(10)
    def test_evaluate_event_context(self) -> None:
        """Stress tests the primary POST /api/v1/events/evaluate endpoint."""
        payload = {
            "chart_data": generate_mock_chart(),
            "event_context": generate_event_context(),
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        with self.client.post(
            "/api/v1/events/evaluate",
            json=payload,
            headers=headers,
            catch_response=True,
            name="POST /api/v1/events/evaluate",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "active_dasha_rulers" in data and "filtered_composite_detections" in data:
                        response.success()
                    else:
                        response.failure(f"Malformed JSON: {data}")
                except Exception as exc:
                    response.failure(f"JSON Parsing Error: {exc}")
            elif response.status_code == 0:
                # Ignore socket disconnects during Locust teardown
                response.ignore()
            else:
                response.failure(
                    f"HTTP {response.status_code}: {response.text}"
                )

    @task(1)
    def test_health_check(self) -> None:
        """Lightweight health check to monitor worker stability under load."""
        self.client.get("/api/v1/health", name="GET /api/v1/health")


# --- Custom Test Execution Hooks ---


@events.test_start.add_listener
def on_test_start(environment: Any, **kwargs: Any) -> None:
    print("\n" + "=" * 60)
    print("🚀 STARTING JRE/JRS ENGINE HIGH-CONCURRENCY LOAD TEST")
    print(f"Target Host: {environment.host}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment: Any, **kwargs: Any) -> None:
    print("\n" + "=" * 60)
    print("🏁 LOAD TEST COMPLETED")
    print("Check summary metrics above for p95/p99 latency targets.")
    print("=" * 60 + "\n")
