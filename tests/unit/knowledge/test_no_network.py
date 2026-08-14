"""Static gate 6: no network modules and no network usage (SPEC §18).

Mirrors the JRE-002/JRE-003 convention: a static import scan plus a runtime
hook asserting ``socket`` is never called during the unit suite.
"""

from __future__ import annotations

from pathlib import Path

import knowledge

SRC = Path(knowledge.__file__).resolve().parent

FORBIDDEN_NETWORK_IMPORTS = (
    "import socket",
    "from socket",
    "import requests",
    "from requests",
    "import urllib",
    "from urllib",
    "import httpx",
    "from httpx",
)


def test_no_network_imports_in_package():
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for fragment in FORBIDDEN_NETWORK_IMPORTS:
            assert fragment not in text, f"{path.name} imports network: {fragment}"


def test_socket_never_called(monkeypatch):
    """The service constructs and synthesizes without touching the network."""
    import socket

    calls: list[str] = []

    def _guard(*args, **kwargs):
        calls.append("socket")
        raise AssertionError("knowledge must never call socket")

    monkeypatch.setattr(socket, "socket", _guard)
    monkeypatch.setattr(socket, "create_connection", _guard)

    service = knowledge.KnowledgeService()
    query = knowledge.RuleQuery(
        domain=knowledge.RuleDomain.YOGA_DEFINITION,
        fact_snapshot={
            "planets": [
                {
                    "body": "MOON",
                    "rashi": "KARKA",
                    "nakshatra": "PUSHYA",
                    "pada": 1,
                    "degree_in_rashi": 5.0,
                    "retrograde": "DIRECT",
                },
            ],
            "lagna": {"rashi": "KARKA", "nakshatra": "PUSHYA", "pada": 1},
            "relative_houses": {"LAGNA": {"MOON": 1}, "MOON": {"MOON": 1}},
            "pairs": [],
        },
        profile_id="bphs-classical",
    )
    service.synthesize(query)
    assert calls == []
