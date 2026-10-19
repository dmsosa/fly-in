"""End-to-end tests for :class:`orchestrator.orchestrator.Orchestrator`.

These tests describe the *intended* behaviour taken from the subject and
``maps/README.md``:

* the output is **one line per turn**, moves separated by spaces
  (``D1-zone1 D2-zone2``);
* a normal / priority move resolves in a single turn;
* a restricted move spans **two** turns: the connection first, the zone
  second;
* ``max_drones`` (zone) and ``max_link_capacity`` (connection) are limits
  that must never be exceeded;
* every drone eventually reaches the end zone.

Because the tests encode intent, a red test points at a bug in the code,
not at a badly written test.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from error import FlyinError
from model.drone import DroneState
from orchestrator.orchestrator import Move
from tests.helpers import make_graph, make_orchestrator


def _turn_as_strings(turn) -> list[str]:
    return [move.to_str() for move in turn]


class TestDroneSetup:
    """What the orchestrator must have built before the first turn."""

    def test_creates_one_drone_per_graph_count(self, orch_pair_linear) -> None:
        assert sorted(orch_pair_linear.drones) == ["D1", "D2"]

    def test_drones_start_on_the_start_zone(self, orch_pair_linear) -> None:
        start = orch_pair_linear.graph.start_zone
        for drone in orch_pair_linear.drones.values():
            assert drone.current_zone is start
            assert drone.state is DroneState.STOP

    def test_start_zone_tracks_every_drone(self, orch_pair_linear) -> None:
        start = orch_pair_linear.graph.start_zone
        assert start.drone_count == 2
        assert start.drones_by_id == ["D1", "D2"]

    def test_get_drone_by_id(self, orch_pair_linear) -> None:
        assert orch_pair_linear.get_drone_by_id("D1").id == "D1"
        assert orch_pair_linear.get_drone_by_id("does-not-exist") is None


class TestGraphIntegrity:
    """Wiring the simulator must not mutate the parsed map."""

    def test_orchestrator_does_not_duplicate_zone_links(self) -> None:
        graph = make_graph(
            drone_count=1,
            start=("start", (0, 0)),
            end=("goal", (2, 0)),
            zones=[{"name": "a", "coord": (1, 0)}],
            connections=[("start", "a"), ("a", "goal")],
        )
        make_orchestrator(graph)

        # Each incident connection must be listed exactly once per zone.
        assert len(graph.start_zone.connections) == 1
        assert len(graph.get_zone_by_name("a").connections) == 2
        assert len(graph.end_zone.connections) == 1


class TestSingleTurnNormalMove:
    """``start -- goal``: the whole trip fits in one turn."""

    def test_records_one_formatted_move(self, orch_linear) -> None:
        moves = orch_linear.next_turn()
        assert _turn_as_strings(moves) == ["D1-goal"]

    def test_drone_lands_on_the_goal(self, orch_linear) -> None:
        orch_linear.next_turn()
        drone = orch_linear.drones["D1"]
        assert drone.current_zone is orch_linear.graph.end_zone
        assert drone.state is DroneState.DELIVERED
        assert drone.move_count == 1

    def test_zone_and_link_occupancy_are_updated(self, orch_linear) -> None:
        graph = orch_linear.graph
        orch_linear.next_turn()
        assert graph.start_zone.drone_count == 0
        assert graph.end_zone.drone_count == 1
        assert graph.get_connection("start", "goal").drone_count == 0

    def test_run_orchestra_ends_after_one_turn(self, orch_linear) -> None:
        history = orch_linear.run_orchestra()
        assert len(history) == 1
        assert orch_linear.turn_count == 1
        assert [_turn_as_strings(turn) for turn in history] == [["D1-goal"]]


class TestMultiTurnNormalMove:
    """``start -- a -- goal``: one zone per turn."""

    def test_first_turn_stops_on_the_intermediate_zone(
        self, orch_two_hop
    ) -> None:
        moves = orch_two_hop.next_turn()
        drone = orch_two_hop.drones["D1"]
        assert _turn_as_strings(moves) == ["D1-a"]
        assert drone.current_zone.name == "a"
        assert drone.state is DroneState.STOP

    def test_second_turn_delivers(self, orch_two_hop) -> None:
        orch_two_hop.next_turn()
        moves = orch_two_hop.next_turn()
        assert _turn_as_strings(moves) == ["D1-goal"]
        assert orch_two_hop.drones["D1"].state is DroneState.DELIVERED

    def test_run_takes_one_turn_per_hop(self, orch_two_hop) -> None:
        history = orch_two_hop.run_orchestra()
        assert [_turn_as_strings(turn) for turn in history] == [
            ["D1-a"],
            ["D1-goal"],
        ]


class TestRestrictedZone:
    """A restricted zone takes two turns to enter (README: '2-turn')."""

    def test_crossing_starts_on_the_first_turn(self, orch_restricted) -> None:
        moves = orch_restricted.next_turn()
        drone = orch_restricted.drones["D1"]
        conn = orch_restricted.graph.get_connection("start", "r")

        assert _turn_as_strings(moves) == ["D1-start-r"]
        assert drone.state is DroneState.FLYIN
        assert conn.drone_count == 1
        # The drone rides the link on turn 1, it is not in the zone yet.
        assert orch_restricted.graph.get_zone_by_name("r").drone_count == 0

    def test_arrival_completes_on_the_second_turn(
        self, orch_restricted
    ) -> None:
        orch_restricted.next_turn()
        moves = orch_restricted.next_turn()
        drone = orch_restricted.drones["D1"]
        r = orch_restricted.graph.get_zone_by_name("r")
        conn = orch_restricted.graph.get_connection("start", "r")

        assert _turn_as_strings(moves) == ["D1-r"]
        assert drone.state is DroneState.STOP
        assert drone.current_zone.name == "r"
        assert r.drone_count == 1
        assert conn.drone_count == 0


class TestCapacity:
    """Hard limits: a zone / a link can never be oversubscribed."""

    def test_zone_max_drones_only_lets_one_in(
        self, orch_zone_capacity
    ) -> None:
        moves = orch_zone_capacity.next_turn()
        a = orch_zone_capacity.graph.get_zone_by_name("a")
        waiting = orch_zone_capacity.drones["D2"]

        assert _turn_as_strings(moves) == ["D1-a"]
        assert a.drone_count == 1
        assert waiting.current_zone is orch_zone_capacity.graph.start_zone
        assert waiting.state is DroneState.WAIT

    def test_link_max_capacity_only_lets_one_cross(
        self, orch_link_capacity
    ) -> None:
        moves = orch_link_capacity.next_turn()
        assert len(moves) == 1
        assert orch_link_capacity.graph.end_zone.drone_count == 1


class TestConnectionLifecycle:
    def test_no_link_is_left_occupied_after_a_run(self, orch_two_hop) -> None:
        orch_two_hop.run_orchestra()
        assert all(c.drone_count == 0 for c in orch_two_hop.graph.connections)


class TestExportTurns:
    """``export_turns`` mirrors the 2D history, one line per turn."""

    def test_one_line_per_turn_with_space_separated_moves(
        self, orch_pair_linear, tmp_path: Path
    ) -> None:
        out = tmp_path / "out.txt"
        orch_pair_linear.output_file = str(out)
        orch_pair_linear.run_orchestra()
        orch_pair_linear.export_turns()

        content = out.read_text(encoding="utf-8")
        assert content.splitlines() == ["D1-goal D2-goal"]

    def test_delivered_moves_never_print_unknown(
        self, orch_linear, tmp_path
    ) -> None:
        orch_linear.output_file = str(tmp_path / "out.txt")
        orch_linear.run_orchestra()
        orch_linear.export_turns()

        content = Path(orch_linear.output_file).read_text(encoding="utf-8")
        assert "Unknown" not in content
        assert content.strip() == "D1-goal"

    def test_export_before_running_raises(self, orch_linear, tmp_path) -> None:
        orch_linear.output_file = str(tmp_path / "out.txt")
        with pytest.raises(FlyinError):
            orch_linear.export_turns()


class TestMoveFormatting:
    """``Move.to_str`` is what the output file is made of, so pin it down."""

    def test_stopped_move_names_its_zone(self) -> None:
        assert Move(0, "D1", "a").to_str() == "D1-a"

    def test_in_flight_move_names_both_ends(self) -> None:
        assert Move(0, "D1", "start-r").to_str() == "D1-start-r"

    def test_delivered_move_names_the_end_zone(self) -> None:
        assert Move(0, "D1", "goal").to_str() == "D1-goal"
