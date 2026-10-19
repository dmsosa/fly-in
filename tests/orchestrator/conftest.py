"""Orchestrator fixtures.

Each fixture builds a tiny map and wires it into an ``Orchestrator`` so the
tests can talk about *turns* and *output* instead of graph plumbing.
"""
from __future__ import annotations

import pytest

from orchestrator.orchestrator import Orchestrator
from tests.helpers import make_graph, make_orchestrator


@pytest.fixture
def orch_linear() -> Orchestrator:
    """``start -- goal`` with a single drone."""
    graph = make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (1, 0)),
        connections=[("start", "goal")],
    )
    return make_orchestrator(graph)


@pytest.fixture
def orch_two_hop() -> Orchestrator:
    """``start -- a -- goal`` with a single drone."""
    graph = make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[{"name": "a", "coord": (1, 0)}],
        connections=[("start", "a"), ("a", "goal")],
    )
    return make_orchestrator(graph)


@pytest.fixture
def orch_restricted() -> Orchestrator:
    """``start -- r(restricted) -- goal`` with a single drone."""
    graph = make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[{"name": "r", "coord": (1, 0), "type": "restricted"}],
        connections=[("start", "r"), ("r", "goal")],
    )
    return make_orchestrator(graph)


@pytest.fixture
def orch_zone_capacity() -> Orchestrator:
    """Two drones racing for an intermediate zone that only holds one.

    The links are wide on purpose so the *zone* is the only bottleneck.
    """
    graph = make_graph(
        drone_count=2,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[{"name": "a", "coord": (1, 0), "max_drones": 1}],
        connections=[
            {"zone_a": "start", "zone_b": "a", "max_link_capacity": 2},
            {"zone_a": "a", "zone_b": "goal", "max_link_capacity": 2},
        ],
        start_max_drones=2,
        end_max_drones=2,
    )
    return make_orchestrator(graph)


@pytest.fixture
def orch_link_capacity() -> Orchestrator:
    """Two drones, one link that only carries one drone per turn."""
    graph = make_graph(
        drone_count=2,
        start=("start", (0, 0)),
        end=("goal", (1, 0)),
        connections=[
            {"zone_a": "start", "zone_b": "goal", "max_link_capacity": 1},
        ],
        start_max_drones=2,
        end_max_drones=2,
    )
    return make_orchestrator(graph)


@pytest.fixture
def orch_pair_linear() -> Orchestrator:
    """Two drones that can reach the goal in the very same turn.

    Used to check that a turn is a *line*, not a move per line.
    """
    graph = make_graph(
        drone_count=2,
        start=("start", (0, 0)),
        end=("goal", (1, 0)),
        connections=[
            {"zone_a": "start", "zone_b": "goal", "max_link_capacity": 2},
        ],
        start_max_drones=2,
        end_max_drones=2,
    )
    return make_orchestrator(graph)
