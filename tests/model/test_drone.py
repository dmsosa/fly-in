"""Tests for :mod:`model.drone`.

The orchestrator owns all the movement logic, so a ``Drone`` is a plain
data holder. What matters here is that it starts clean, that its
``last_visited`` memory is per-drone and bounded, and that the memory is
what the orchestrator reads to avoid short cycles.
"""
from __future__ import annotations

from model.drone import VISITED_MEMORY, Drone, DroneState


class TestDroneDefaults:
    def test_starts_stopped_with_no_target(self) -> None:
        drone = Drone(id="D1")

        assert drone.state is DroneState.STOP
        assert drone.current_zone is None
        assert drone.target is None
        assert drone.connection is None
        assert drone.move_count == 0
        assert drone.wait_count == 0
        assert list(drone.last_visited) == []

    def test_accepts_a_starting_zone(self) -> None:
        from model.graph import Zone

        start = Zone(name="start", coord=(0, 0), hub_type="start")
        drone = Drone(id="D1", current_zone=start)

        assert drone.current_zone is start


class TestVisitedMemory:
    def test_remember_appends_to_the_window(self) -> None:
        drone = Drone(id="D1")
        drone.remember("a")
        drone.remember("b")

        assert list(drone.last_visited) == ["a", "b"]
        assert drone.has_visited("a") is True
        assert drone.has_visited("z") is False

    def test_memory_is_bounded(self) -> None:
        drone = Drone(id="D1")
        for name in ["a", "b", "c", "d"]:
            drone.remember(name)

        assert len(drone.last_visited) == VISITED_MEMORY
        assert list(drone.last_visited) == ["b", "c", "d"]

    def test_old_zones_leave_the_window(self) -> None:
        drone = Drone(id="D1")
        drone.remember("a")
        drone.remember("b")
        drone.remember("c")
        drone.remember("d")
        # ``a`` has been pushed out of the memory window.
        assert drone.has_visited("a") is False
        assert drone.has_visited("d") is True

    def test_memory_is_not_shared_between_drones(self) -> None:
        first = Drone(id="D1")
        second = Drone(id="D2")
        first.remember("x")
        assert list(first.last_visited) == ["x"]
        assert list(second.last_visited) == []
