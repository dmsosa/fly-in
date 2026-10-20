"""Unsolvable maps must be refused up front, not played into a deadlock.

A disconnected graph (or one whose only exit is blocked) can never be
scheduled: every drone would simply wait. The orchestrator checks the
pathfinder's distance map *before* the first turn and raises
``FlyinUnreachableError`` instead of dying later on the much vaguer
"every drone is waiting" deadlock error.
"""
from __future__ import annotations

import pytest

from error.error import FlyinUnreachableError
from model.drone import DroneState
from model.graph import FlyinGraph
from tests.helpers import make_orchestrator


def test_disconnected_map_raises_before_the_first_turn(
    disconnected_graph: FlyinGraph,
) -> None:
    orch = make_orchestrator(disconnected_graph)
    with pytest.raises(FlyinUnreachableError) as excinfo:
        orch.run_orchestra()

    assert orch.turn_count == 0
    assert orch.history == []
    message = str(excinfo.value)
    assert "start" in message and "goal" in message
    assert "a" in message  # the stranded zone is named in the report


def test_blocked_route_counts_as_unreachable(
    blocked_dead_end_graph: FlyinGraph,
) -> None:
    """Blocked zones are never traversed, so they cut the graph too."""
    orch = make_orchestrator(blocked_dead_end_graph)
    with pytest.raises(FlyinUnreachableError):
        orch.run_orchestra()


def test_isolated_island_does_not_break_the_run(
    island_graph: FlyinGraph,
) -> None:
    """A map stays solvable when only *extra* zones are disconnected."""
    orch = make_orchestrator(island_graph)
    history = orch.run_orchestra()

    assert history, "the delivery itself must still happen"
    assert all(
        drone.state is DroneState.DELIVERED
        for drone in orch.drones.values()
    )
    assert orch.pathfinding.unreachable_zones() == ["island"]


def test_reachable_map_does_not_raise(
    linear_graph: FlyinGraph,
) -> None:
    orch = make_orchestrator(linear_graph)
    assert orch.run_orchestra()
