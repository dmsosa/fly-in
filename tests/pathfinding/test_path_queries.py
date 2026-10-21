"""Tests for the whole-path queries on ``DijkstraPathfinding``.

Both methods take no arguments: they answer for the graph's own start/end
hubs.

``find_shortest_path() -> list[str]``
    Zone *names* from ``graph.start_zone`` to ``graph.end_zone`` whose total
    ``static_cost`` is minimal (equal to ``distance_map[start]``), with both
    endpoints included exactly once. ``[]`` when no route exists.

``find_all_paths() -> list[list[str]]``
    Every *simple* path between the two hubs (no zone twice), endpoints
    included, no duplicates. ``[]`` when no route exists.

``_build_path`` is the helper both methods rely on, so it is pinned down
directly as well.
"""
from __future__ import annotations

import math
import typing

import pytest

from model.graph import FlyinGraph
from pathfinding.dijkstra import DijkstraPathfinding
from tests.helpers import make_graph


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


# ---- shared helper -------------------------------------------------------
class TestBuildPath:
    """``_build_path`` turns a parent map into a start-to-end path."""

    def test_single_zone(self) -> None:
        assert DijkstraPathfinding._build_path(
            "start", {"start": None}
        ) == ["start"]

    def test_includes_both_endpoints_once(self) -> None:
        parents = {"start": None, "a": "start", "goal": "a"}
        assert DijkstraPathfinding._build_path(
            "goal", parents
        ) == ["start", "a", "goal"]

    def test_longer_chain(self) -> None:
        parents = {"start": None, "a": "start", "b": "a", "goal": "b"}
        assert DijkstraPathfinding._build_path(
            "goal", parents
        ) == ["start", "a", "b", "goal"]


# ---- find_shortest_path --------------------------------------------------
class TestFindShortestPath:
    def test_reaches_the_goal_at_all(self, linear_graph: FlyinGraph) -> None:
        """The most basic contract: a usable path comes back."""
        pf = DijkstraPathfinding(linear_graph)
        assert pf.find_shortest_path() == ["start", "a", "b", "goal"]

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
            "island_graph",
        ],
    )
    def test_has_the_optimal_cost(
        self, fixture_name: str, request: pytest.FixtureRequest
    ) -> None:
        """Cost of the path must equal the pre-computed distance map."""
        graph: FlyinGraph = request.getfixturevalue(fixture_name)
        pf = DijkstraPathfinding(graph)

        path = pf.find_shortest_path()
        assert_valid_path(graph, path, "start", "goal")
        assert zone_cost(graph, path) == pytest.approx(
            pf.distance_map["start"]
        )

    def test_cost_is_strictly_decreasing_along_the_path(
        self, diamond_graph: FlyinGraph
    ) -> None:
        """On a shortest path every step must reduce the cost-to-go."""
        pf = DijkstraPathfinding(diamond_graph)
        path = pf.find_shortest_path()

        remaining = [pf.distance_map[name] for name in path]
        for before, after in zip(remaining, remaining[1:]):
            assert after < before

    def test_prefers_the_cheaper_priority_branch(
        self, priority_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(priority_graph)
        path = pf.find_shortest_path()

        assert path == ["start", "p", "goal"]
        assert zone_cost(priority_graph, path) == pytest.approx(1.5)

    def test_never_crosses_a_blocked_zone(
        self, blocked_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(blocked_graph)
        assert "wall" not in pf.find_shortest_path()

    def test_unreachable_goal_returns_empty(
        self, disconnected_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(disconnected_graph)
        assert pf.find_shortest_path() == []

    def test_path_on_a_cyclic_graph_has_no_repetition(
        self, cycle_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(cycle_graph)
        path = pf.find_shortest_path()
        assert_valid_path(cycle_graph, path, "start", "goal")

    def test_result_is_deterministic(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        assert pf.find_shortest_path() == pf.find_shortest_path()

    def test_return_annotation_matches_reality(self) -> None:
        hints = typing.get_type_hints(DijkstraPathfinding.find_shortest_path)
        assert hints["return"] == list[str]


# ---- find_all_paths ------------------------------------------------------
class TestFindAllPaths:
    def test_returns_lists_of_names(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        paths = pf.find_all_paths()
        assert paths
        for path in paths:
            assert isinstance(path, list)
            assert all(isinstance(name, str) for name in path)

    def test_return_annotation_matches_reality(self) -> None:
        """It returns paths, not zones: ``list[list[str]]``."""
        hints = typing.get_type_hints(DijkstraPathfinding.find_all_paths)
        assert hints["return"] == list[list[str]]

    def test_linear_map_has_one_path(
        self, linear_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(linear_graph)
        assert pf.find_all_paths() == [["start", "a", "b", "goal"]]

    def test_diamond_map_has_two_paths(
        self, diamond_graph: FlyinGraph
    ) -> None:
        """Two independent routes must both be listed."""
        pf = DijkstraPathfinding(diamond_graph)
        found = {tuple(path) for path in pf.find_all_paths()}
        assert found == {
            ("start", "a", "goal"),
            ("start", "b", "goal"),
        }

    def test_fork_map_lists_both_routes(
        self, fork_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(fork_graph)
        found = {tuple(path) for path in pf.find_all_paths()}
        assert found == {
            ("start", "a", "goal"),
            ("start", "c", "d", "e", "goal"),
        }

    def test_cycle_map_returns_simple_paths_only(
        self, cycle_graph: FlyinGraph
    ) -> None:
        """A cycle must not produce an infinite family of walks."""
        pf = DijkstraPathfinding(cycle_graph)
        found = {tuple(path) for path in pf.find_all_paths()}
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

        paths = pf.find_all_paths()
        assert paths, "these maps do have routes"
        for path in paths:
            assert_valid_path(graph, path, "start", "goal")

    def test_no_path_is_reported_twice(
        self, diamond_graph: FlyinGraph
    ) -> None:
        """The goal can be queued several times: no repeat rows allowed."""
        pf = DijkstraPathfinding(diamond_graph)
        paths = pf.find_all_paths()
        assert len(paths) == len({tuple(path) for path in paths})

    def test_no_route_is_lost_between_two_branches(
        self, diamond_graph: FlyinGraph
    ) -> None:
        """Every enumerated path must be distinct, not one path twice."""
        pf = DijkstraPathfinding(diamond_graph)
        paths = pf.find_all_paths()
        assert len(paths) == 2
        assert paths[0] != paths[1]

    def test_each_route_appears_exactly_once(
        self, cycle_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(cycle_graph)
        paths = pf.find_all_paths()
        assert len(paths) == 2
        assert len({tuple(path) for path in paths}) == 2

    def test_never_crosses_a_blocked_zone(
        self, blocked_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(blocked_graph)
        for path in pf.find_all_paths():
            assert "wall" not in path

    def test_unreachable_goal_returns_empty(
        self, disconnected_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(disconnected_graph)
        assert pf.find_all_paths() == []

    def test_result_is_deterministic(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        assert pf.find_all_paths() == pf.find_all_paths()

    def test_contains_the_shortest_path(
        self, diamond_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(diamond_graph)
        paths = pf.find_all_paths()
        best = pf.find_shortest_path()

        assert tuple(best) in {tuple(path) for path in paths}
        cheapest = min(zone_cost(diamond_graph, p) for p in paths)
        assert cheapest == pytest.approx(zone_cost(diamond_graph, best))

    def test_all_costs_are_finite(
        self, cycle_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(cycle_graph)
        for path in pf.find_all_paths():
            assert math.isfinite(zone_cost(cycle_graph, path))
