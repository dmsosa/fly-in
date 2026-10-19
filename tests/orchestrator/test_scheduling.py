"""Scheduling behaviour: capacity, progress, anti-ping-pong, deadlocks.

These tests exercise the *orchestrator* (not a single drone) because the
interesting failures only show up when several drones share bottlenecks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from error import FlyinError
from orchestrator.orchestrator import Orchestrator
from tests.helpers import make_graph, make_orchestrator

MAPS = Path(__file__).resolve().parents[2] / "maps"


def _assert_capacities_hold(orch: Orchestrator) -> None:
    """No zone / link may be oversubscribed after a turn."""
    for zone in orch.graph.all_zones:
        if zone.is_unlimited_capacity():
            continue
        assert zone.drone_count <= zone.max_drones, zone.name

    turn = orch.turn_count
    for conn in orch.graph.connections:
        used = (
            conn.drone_count
            + orch.reservation_table.link_occupancy.get((conn.key, turn), 0)
        )
        assert used <= conn.max_link_capacity, conn.key


def _run_step_by_step(orch: Orchestrator) -> list:
    history = []
    while orch._continue():
        moves = orch.next_turn()
        assert moves, "a live schedule must never emit an empty turn"
        _assert_capacities_hold(orch)
        orch.turn_count += 1
        history.append(moves)
        assert orch.turn_count < 10_000, "run did not converge"
    return history


# ---- neighbour selection ------------------------------------------------


def _diamond_graph():
    """``start`` splits into ``a`` / ``b``, both one hop from ``goal``."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[
            {"name": "a", "coord": (1, 1)},
            {"name": "b", "coord": (1, -1)},
        ],
        connections=[
            ("start", "a"),
            ("a", "goal"),
            ("start", "b"),
            ("b", "goal"),
        ],
    )


def test_prefers_a_neighbour_it_has_not_visited() -> None:
    graph = _diamond_graph()
    orch = make_orchestrator(graph)
    drone = orch.drones["D1"]
    drone.last_visited.append("a")  # pretend the drone just came from "a"

    chosen, _ = orch._choose_next(drone, graph.start_zone, 0)
    assert chosen is not None
    assert chosen.name == "b"


def test_falls_back_to_closest_when_all_are_visited() -> None:
    graph = _diamond_graph()
    orch = make_orchestrator(graph)
    drone = orch.drones["D1"]
    drone.last_visited.extend(["a", "b"])

    chosen, _ = orch._choose_next(drone, graph.start_zone, 0)
    assert chosen is not None
    assert chosen.name == "a"  # deterministic best of a tie


def test_choose_next_never_walks_away_from_the_goal() -> None:
    graph = make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (1, 0)),
        zones=[{"name": "dead", "coord": (0, 1)}],
        connections=[("start", "goal"), ("start", "dead")],
    )
    orch = make_orchestrator(graph)

    chosen, _ = orch._choose_next(orch.drones["D1"], graph.start_zone, 0)
    assert chosen is not None
    assert chosen.name == "goal"


def test_choose_next_honours_zone_capacity() -> None:
    graph = _diamond_graph()
    graph.get_zone_by_name("a").drone_count = 1  # "a" is full
    orch = make_orchestrator(graph)

    chosen, _ = orch._choose_next(orch.drones["D1"], graph.start_zone, 0)
    assert chosen is not None
    assert chosen.name == "b"


# ---- deadlocks ----------------------------------------------------------


def test_impossible_map_is_reported_as_a_deadlock(
    blocked_dead_end_graph,
) -> None:
    orch = make_orchestrator(blocked_dead_end_graph)
    with pytest.raises(FlyinError):
        orch.run_orchestra()


# ---- anti-ping-pong / progress -----------------------------------------


def test_no_drone_ever_moves_away_from_the_goal() -> None:
    """Across a full run every hop lowers the distance to the goal.

    That monotonic property is what makes ping-pong impossible: a drone
    can not bounce between two zones because that would require a move
    that does not decrease the cost-to-go.
    """
    data_graph = make_graph(
        drone_count=4,
        start=("start", (0, 0)),
        end=("goal", (3, 0)),
        zones=[
            {"name": "a", "coord": (1, 0)},
            {"name": "b", "coord": (2, 0)},
            {"name": "loop", "coord": (1, 1)},
        ],
        connections=[
            ("start", "a"),
            ("a", "b"),
            ("b", "goal"),
            ("start", "loop"),
            ("loop", "goal"),
        ],
        start_max_drones=4,
    )
    orch = make_orchestrator(data_graph)
    distance_map = orch.pathfinding.distance_map

    positions = {d.id: [d.current_zone.name] for d in orch.drones.values()}
    while orch._continue():
        orch.next_turn()
        orch.turn_count += 1
        for drone in orch.drones.values():
            if drone.current_zone is None:
                continue
            name = drone.current_zone.name
            if positions[drone.id][-1] != name:
                positions[drone.id].append(name)

    for drone in orch.drones.values():
        assert drone.state.name == "DELIVERED"
        path = positions[drone.id]
        distances = [distance_map[n] for n in path]
        assert all(
            later < earlier
            for earlier, later in zip(distances, distances[1:])
        ), f"{drone.id} did not make steady progress: {positions[drone.id]}"


# ---- full-map integration ----------------------------------------------


def test_challenger_map_is_completely_solved() -> None:
    """The stress-test map must be solved without deadlocking."""
    from parser import FlyinParser
    from model.graph import FlyinGraph
    from pathfinding import DijkstraPathfinding

    path = MAPS / "challenger" / "01_the_impossible_dream.txt"
    if not path.exists():
        pytest.skip("challenger map is not available")

    graph = FlyinGraph(**FlyinParser().parse(path))
    orch = Orchestrator(graph, DijkstraPathfinding(graph))

    history = _run_step_by_step(orch)

    assert orch.turn_count == len(history)
    assert all(
        d.state.name == "DELIVERED" for d in orch.drones.values()
    )
    assert len(orch.drones) == 25
    # Sanity ceiling: the map should be solved in well under this.
    assert orch.turn_count < 1000
