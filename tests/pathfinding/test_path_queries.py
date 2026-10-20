"""Tests for the whole-path queries on ``DijkstraPathfinding``.

These two methods do not exist yet; the tests define the contract they are
expected to honour and are skipped until the methods appear, so the suite
stays green in the meantime.

Contract
--------
``find_shortest_path(start: str, end: str) -> list[str]``
    Zone *names*, both endpoints included, whose total ``static_cost`` is
    minimal.  ``[]`` when no route exists (or a name is unknown).  A start
    equal to the end yields ``[start]``.

``find_all_paths(start: str, end: str) -> list[list[str]]``
    Every *simple* path (no zone visited twice) between the two names, as
    lists of names, endpoints included.  Current implementation order is not
    assumed -- paths are compared as sets -- but repeated calls must agree.
"""
from __future__ import annotations

import math

import pytest

from model.graph import FlyinGraph
from pathfinding.dijkstra import DijkstraPathfinding
from tests.helpers import make_graph

needs_shortest_path = pytest.mark.skipif(
    not hasattr(DijkstraPathfinding, "find_shortest_path"),
    reason="DijkstraPathfinding.find_shortest_path is not implemented",
)
needs_all_paths = pytest.mark.skipif(
    not hasattr(DijkstraPathfinding, "find_all_paths"),
    reason="DijkstraPathfinding.find_all_paths is not implemented",
)


# ---- helpers ------------------------------------------------------------
def zone_cost(graph: FlyinGraph, path: list[str]) -> float:
    """Total cost of entering every zone of ``path`` after the first one."""
    total = 0.0
    for name in path[1:]:
        zone = graph.get_zone_by_name(name)
        assert zone is not None, f"path uses unknown zone {name!r}"
        total += zone.static_cost
    return total


def assert_valid_path(
    graph: FlyinGraph, path: list[str], start: str, end: str
) -> None:
    """Structural checks every returned path must pass."""
    assert path, "a returned path must never be empty"
    assert path[0] == start, f"path must start at {start!r}: {path}"
    assert path[-1] == end, f"path must end at {end!r}: {path}"
    assert len(path) == len(set(path)), f"path repeats a zone: {path}"

    for origin, target in zip(path, path[1:]):
        neighbours = {
            neighbour.name
            for neighbour in graph.get_neighbors(origin)
        }
        assert target in neighbours, f"{origin!r} -> {target!r} is no link"
        zone = graph.get_zone_by_name(target)
        assert zone is not None
        assert not zone.is_blocked(), f"path crosses blocked {target!r}"


# ---- local fixtures ------------------------------------------------------
@pytest.fixture
def diamond_graph() -> FlyinGraph:
    """``start -> {a, b} -> goal``: exactly two distinct routes."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (4, 0)),
        zones=[
            {"name": "a", "coord": (1, 1)},
            {"name": "b", "coord": (1, -1)},
        ],
        connections=[
            ("start", "a"), ("a", "goal"),
            ("start", "b"), ("b", "goal"),
        ],
    )


@pytest.fixture
def priority_graph() -> FlyinGraph:
    """Two routes: via ``p`` (priority) is cheaper than via ``n``."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[
            {"name": "n", "coord": (1, 1)},
            {"name": "p", "coord": (1, -1), "type": "priority"},
        ],
        connections=[
            ("start", "n"), ("n", "goal"),
            ("start", "p"), ("p", "goal"),
        ],
    )


@pytest.fixture
def cycle_graph() -> FlyinGraph:
    """A triangle plus the goal: two simple routes, many walks."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (3, 0)),
        zones=[
            {"name": "a", "coord": (1, 1)},
            {"name": "b", "coord": (2, 1)},
        ],
        connections=[
            ("start", "a"), ("a", "b"), ("b", "start"), ("b", "goal"),
        ],
    )


# ---- find_shortest_path --------------------------------------------------
@needs_shortest_path
class TestFindShortestPath:
    def test_follows_the_only_route(self, linear_graph: FlyinGraph) -> None:
        pf = DijkstraPathfinding(linear_graph)
        path = pf.find_shortest_path("start", "goal")
        assert path == ["start", "a", "b", "goal"]

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "linear_graph",
            "restricted_graph",
            "fork_graph",
            "blocked_graph",
            "diamond_graph",
            "priority_graph",
            "cycle_graph",
        ],
    )
    def test_has_the_optimal_cost(
        self, fixture_name: str, request: pytest.FixtureRequest
    ) -> None:
        """Cost of the path must equal the pre-computed distance map."""
        graph: FlyinGraph = request.getfixturevalue(fixture_name)
        pf = DijkstraPathfinding(graph)

        path = pf.find_shortest_path("start", "goal")
        assert_valid_path(graph, path, "start", "goal")
        assert zone_cost(graph, path) == pytest.approx(
            pf.distance_map["start"]
        )

    def test_cost_is_strictly_decreasing_along_the_path(
        self, diamond_graph: FlyinGraph
    ) -> None:
        """On a shortest path every step must reduce the cost-to-go."""
        pf = DijkstraPathfinding(diamond_graph)
        path = pf.find_shortest_path("start", "goal")

        remaining = [pf.distance_map[name] for name in path]
        for before, after in zip(remaining, remaining[1:]):
            assert after < before

    def test_prefers_the_cheaper_priority_branch(
        self, priority_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(priority_graph)
        path = pf.find_shortest_path("start", "goal")

        assert "p" in path
        assert "n" not in path
        assert zone_cost(priority_graph, path) == pytest.approx(1.5)

    def test_never_crosses_a_blocked_zone(
        self, blocked_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(blocked_graph)
        path = pf.find_shortest_path("start", "goal")
        assert "wall" not in path

    def test_start_equal_to_end(self, linear_graph: FlyinGraph) -> None:
        pf = DijkstraPathfinding(linear_graph)
        assert pf.find_shortest_path("start", "start") == ["start"]

    def test_unreachable_goal_returns_empty(
        self, disconnected_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(disconnected_graph)
        assert pf.find_shortest_path("start", "goal") == []

    def test_unknown_zone_returns_empty(
        self, linear_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(linear_graph)
        assert pf.find_shortest_path("start", "nope") == []
        assert pf.find_shortest_path("nope", "goal") == []

    def test_path_on_a_cyclic_graph_has_no_repetition(
        self, cycle_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(cycle_graph)
        path = pf.find_shortest_path("start", "goal")
        assert_valid_path(cycle_graph, path, "start", "goal")


# ---- find_all_paths ------------------------------------------------------
@needs_all_paths
class TestFindAllPaths:
    def test_linear_map_has_one_path(
        self, linear_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(linear_graph)
        assert pf.find_all_paths("start", "goal") == [
            ["start", "a", "b", "goal"]
        ]

    def test_diamond_map_has_two_paths(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        found = {tuple(path) for path in pf.find_all_paths("start", "goal")}
        assert found == {
            ("start", "a", "goal"),
            ("start", "b", "goal"),
        }

    def test_cycle_map_returns_simple_paths_only(
        self, cycle_graph: FlyinGraph
    ) -> None:
        """A cycle must not produce an infinite family of walks."""
        pf = DijkstraPathfinding(cycle_graph)
        found = {tuple(path) for path in pf.find_all_paths("start", "goal")}
        assert found == {
            ("start", "b", "goal"),
            ("start", "a", "b", "goal"),
        }

    @pytest.mark.parametrize(
        "fixture_name", ["diamond_graph", "fork_graph", "cycle_graph"]
    )
    def test_every_path_is_valid(
        self, fixture_name: str, request: pytest.FixtureRequest
    ) -> None:
        graph: FlyinGraph = request.getfixturevalue(fixture_name)
        pf = DijkstraPathfinding(graph)

        paths = pf.find_all_paths("start", "goal")
        assert paths, "these maps do have routes"
        for path in paths:
            assert_valid_path(graph, path, "start", "goal")

    def test_no_path_is_reported_twice(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        paths = pf.find_all_paths("start", "goal")
        assert len(paths) == len({tuple(path) for path in paths})

    def test_never_crosses_a_blocked_zone(
        self, blocked_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(blocked_graph)
        for path in pf.find_all_paths("start", "goal"):
            assert "wall" not in path

    def test_unreachable_goal_returns_empty(
        self, disconnected_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(disconnected_graph)
        assert pf.find_all_paths("start", "goal") == []

    def test_result_is_deterministic(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        first = pf.find_all_paths("start", "goal")
        second = pf.find_all_paths("start", "goal")
        assert first == second

    @needs_shortest_path
    def test_contains_the_shortest_path(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        paths = pf.find_all_paths("start", "goal")
        best = pf.find_shortest_path("start", "goal")

        assert tuple(best) in {tuple(path) for path in paths}
        cheapest = min(zone_cost(diamond_graph, p) for p in paths)
        assert cheapest == pytest.approx(zone_cost(diamond_graph, best))

    def test_all_costs_are_finite(
        self, cycle_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(cycle_graph)
        for path in pf.find_all_paths("start", "goal"):
            assert math.isfinite(zone_cost(cycle_graph, path))
