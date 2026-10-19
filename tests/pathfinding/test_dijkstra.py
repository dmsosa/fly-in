"""Tests for :class:`pathfinding.dijkstra.DijkstraPathfinding`."""
from __future__ import annotations

import math

from model.graph import FlyinGraph
from pathfinding.dijkstra import DijkstraPathfinding


class TestDistanceMap:
    def test_linear_distances(self, linear_graph: FlyinGraph) -> None:
        pf = DijkstraPathfinding(linear_graph)
        assert pf.distance_map["goal"] == 0
        assert pf.distance_map["b"] == 1
        assert pf.distance_map["a"] == 2
        assert pf.distance_map["start"] == 3

    def test_restricted_zone_costs_two(self, restricted_graph: FlyinGraph):
        pf = DijkstraPathfinding(restricted_graph)
        assert pf.distance_map["r"] == 2
        assert pf.distance_map["start"] == 3

    def test_blocked_zone_is_not_in_the_map(
        self, blocked_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(blocked_graph)
        assert pf.distance_map.get("wall", math.inf) == math.inf

    def test_unreachable_zone_is_infinite(
        self, island_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(island_graph)
        assert pf.distance_map["island"] == math.inf


class TestFindBestZone:
    def test_picks_the_closest_neighbour(self, fork_graph: FlyinGraph):
        pf = DijkstraPathfinding(fork_graph)
        start = fork_graph.get_zone_by_name("start")
        best = pf.find_best_zone(start)
        assert best is not None
        assert best.name == "a"

    def test_skips_blocked_neighbours(self, blocked_graph: FlyinGraph):
        pf = DijkstraPathfinding(blocked_graph)
        start = blocked_graph.get_zone_by_name("start")
        best = pf.find_best_zone(start)
        assert best is not None
        assert best.name == "a"

    def test_returns_none_when_stuck(
        self, blocked_dead_end_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(blocked_dead_end_graph)
        start = blocked_dead_end_graph.get_zone_by_name("start")
        assert pf.find_best_zone(start) is None


class TestFindBestZoneInvariants:
    """Rules that must hold for *any* choice, regardless of strategy."""

    def test_never_returns_the_current_zone(self, fork_graph: FlyinGraph):
        pf = DijkstraPathfinding(fork_graph)
        current = fork_graph.get_zone_by_name("d")
        best = pf.find_best_zone(current)
        assert best is None or best.name != "d"

    def test_returns_a_connected_neighbour(self, fork_graph: FlyinGraph):
        pf = DijkstraPathfinding(fork_graph)
        current = fork_graph.get_zone_by_name("d")
        neighbours = {
            conn.get_opposite("d") for conn in current.connections
        }
        best = pf.find_best_zone(current)
        assert best is not None
        assert best.name in neighbours

    def test_never_returns_a_blocked_neighbour(
        self, blocked_graph: FlyinGraph
    ):
        pf = DijkstraPathfinding(blocked_graph)
        start = blocked_graph.get_zone_by_name("start")
        best = pf.find_best_zone(start)
        assert best is not None
        assert best.name != "wall"

    def test_is_deterministic(self, fork_graph: FlyinGraph):
        pf = DijkstraPathfinding(fork_graph)
        start = fork_graph.get_zone_by_name("start")
        first = pf.find_best_zone(start)
        second = pf.find_best_zone(start)
        assert first.name == second.name

    def test_prefers_the_branch_closer_to_the_goal(
        self, fork_graph: FlyinGraph
    ):
        """The cheap branch wins even when a costlier one is listed last."""
        pf = DijkstraPathfinding(fork_graph)
        start = fork_graph.get_zone_by_name("start")

        reachable = [
            fork_graph.get_zone_by_name(conn.get_opposite("start"))
            for conn in start.connections
        ]
        reachable = [zone for zone in reachable if not zone.is_blocked()]
        cheapest = min(pf.distance_map[zone.name] for zone in reachable)

        best = pf.find_best_zone(start)
        assert best is not None
        assert pf.distance_map[best.name] == cheapest


class TestAdjacencyList:
    def test_weight_is_the_cost_to_enter_the_neighbour(
        self, restricted_graph: FlyinGraph
    ) -> None:
        pf = DijkstraPathfinding(restricted_graph)
        for neighbours in pf._edges.values():
            for neighbour, weight in neighbours:
                zone = restricted_graph.get_zone_by_name(neighbour)
                assert weight == zone.static_cost

    def test_is_symmetric(self, linear_graph: FlyinGraph) -> None:
        pf = DijkstraPathfinding(linear_graph)
        for name, neighbours in pf._edges.items():
            for neighbour, _ in neighbours:
                reverse = {n for n, _ in pf._edges[neighbour]}
                assert name in reverse
