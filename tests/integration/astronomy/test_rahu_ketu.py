"""QA requirement 10: Rahu and Ketu handling.

- Ketu = Rahu + 180 deg exactly (mod 360), derived from the same node.
- Ketu inherits the node's latitude, distance and speeds.
- MEAN vs TRUE node are distinct; both deterministic.
"""

from __future__ import annotations

import pytest
from tests.integration.astronomy.conftest import make_request

from astronomy.models import BodyId, CalculationConfig, NodeType


def _pair(result):
    rahu = next(p for p in result.positions if p.body is BodyId.RAHU)
    ketu = next(p for p in result.positions if p.body is BodyId.KETU)
    return rahu, ketu


@pytest.mark.parametrize("node_type", [NodeType.MEAN, NodeType.TRUE])
def test_ketu_is_rahu_plus_180(service, node_type):
    result = service.compute(make_request(config=CalculationConfig(node_type=node_type)))
    rahu, ketu = _pair(result)
    delta = (ketu.longitude_tropical - rahu.longitude_tropical) % 360.0
    assert delta == pytest.approx(180.0, abs=1e-9)
    sid_delta = (ketu.longitude_sidereal - rahu.longitude_sidereal) % 360.0
    assert sid_delta == pytest.approx(180.0, abs=1e-9)


@pytest.mark.parametrize("node_type", [NodeType.MEAN, NodeType.TRUE])
def test_ketu_inherits_node_latitude_and_speeds(service, node_type):
    result = service.compute(make_request(config=CalculationConfig(node_type=node_type)))
    rahu, ketu = _pair(result)
    assert ketu.latitude == pytest.approx(rahu.latitude, abs=1e-12)
    assert ketu.distance_au == pytest.approx(rahu.distance_au, abs=1e-12)
    assert ketu.speed_longitude == pytest.approx(rahu.speed_longitude, abs=1e-12)
    assert ketu.speed_latitude == pytest.approx(rahu.speed_latitude, abs=1e-12)
    assert ketu.speed_distance == pytest.approx(rahu.speed_distance, abs=1e-12)


def test_mean_and_true_nodes_differ(service):
    mean = service.compute(make_request(config=CalculationConfig(node_type=NodeType.MEAN)))
    true = service.compute(make_request(config=CalculationConfig(node_type=NodeType.TRUE)))
    rahu_mean, _ = _pair(mean)
    rahu_true, _ = _pair(true)
    assert abs(rahu_mean.longitude_tropical - rahu_true.longitude_tropical) > 0.01


def test_nodes_are_deterministic(service):
    config = CalculationConfig(node_type=NodeType.TRUE)
    first = service.compute(make_request(config=config))
    second = service.compute(make_request(config=config))
    assert first.positions == second.positions
