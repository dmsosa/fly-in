"""Unit tests for :class:`orchestrator.reservation_table.ReservationTable`.

The table is the single place the orchestrator asks "may this drone enter
this zone / cross this link?". These tests pin down its contract:

* zone occupancy is *persistent* (a drone holds its slot until it leaves);
* link occupancy is *per turn* for instantaneous hops, on top of the
  persistent count of drones currently crossing a restricted link;
* the start/end hubs are never a bottleneck.
"""
from __future__ import annotations

from model.graph import Connection, Zone
from orchestrator.reservation_table import ReservationTable
from tests.helpers import make_graph


def make_zone(name: str = "a", **kwargs) -> Zone:
    return Zone(name=name, coord=(0, 0), **kwargs)


class TestZoneReservations:
    def test_empty_zone_is_available(self) -> None:
        table = ReservationTable()
        assert table.is_zone_available(make_zone(max_drones=1), 0, False)

    def test_full_zone_is_not_available(self) -> None:
        table = ReservationTable()
        zone = make_zone(max_drones=1)
        table.reserve_zone(zone, 0)
        assert zone.drone_count == 1
        assert not table.is_zone_available(zone, 1, False)

    def test_release_frees_the_slot(self) -> None:
        table = ReservationTable()
        zone = make_zone(max_drones=1)
        table.reserve_zone(zone, 0)
        table.release_zone(zone, 0)
        assert zone.drone_count == 0
        assert table.is_zone_available(zone, 1, False)

    def test_capacity_scales_with_max_drones(self) -> None:
        table = ReservationTable()
        zone = make_zone(max_drones=2)
        table.reserve_zone(zone, 0)
        assert table.is_zone_available(zone, 1, False)
        table.reserve_zone(zone, 1)
        assert not table.is_zone_available(zone, 2, False)

    def test_zone_stays_occupied_across_turns(self) -> None:
        """A drone that never leaves keeps its slot on every later turn."""
        table = ReservationTable()
        zone = make_zone(max_drones=1)
        table.reserve_zone(zone, 0)
        for turn in range(1, 10):
            assert not table.is_zone_available(zone, turn, False)

    def test_start_or_end_is_always_available(self) -> None:
        table = ReservationTable()
        zone = make_zone(max_drones=1)
        table.reserve_zone(zone, 0)
        assert table.is_zone_available(zone, 0, True)

    def test_unlimited_zone_is_never_a_bottleneck(self) -> None:
        table = ReservationTable()
        zone = make_zone(name="start", max_drones=None)
        assert zone.is_unlimited_capacity()
        for _ in range(50):
            table.reserve_zone(zone, 0)
        assert table.is_zone_available(zone, 0, False)

    def test_release_never_goes_negative(self) -> None:
        table = ReservationTable()
        zone = make_zone(max_drones=1)
        table.release_zone(zone, 0)
        assert zone.drone_count == 0


class TestLinkReservations:
    def test_instantaneous_hops_are_counted_per_turn(self) -> None:
        table = ReservationTable()
        conn = Connection(zone_a="a", zone_b="b", max_link_capacity=1)
        assert table.is_link_available(conn, 0)
        table.reserve_link(conn, 0)
        assert not table.is_link_available(conn, 0)
        # A new turn starts with a clean instantaneous ledger.
        assert table.is_link_available(conn, 1)

    def test_persistent_in_flight_count_is_added(self) -> None:
        table = ReservationTable()
        conn = Connection(zone_a="a", zone_b="b", max_link_capacity=1)
        conn.drone_count = 1  # a drone is crossing the restricted link
        assert not table.is_link_available(conn, 0)
        conn.drone_count = 0
        assert table.is_link_available(conn, 0)

    def test_link_capacity_two_allows_two_hops(self) -> None:
        table = ReservationTable()
        conn = Connection(zone_a="a", zone_b="b", max_link_capacity=2)
        table.reserve_link(conn, 0)
        assert table.is_link_available(conn, 0)
        table.reserve_link(conn, 0)
        assert not table.is_link_available(conn, 0)

    def test_release_link_undoes_a_hop(self) -> None:
        table = ReservationTable()
        conn = Connection(zone_a="a", zone_b="b", max_link_capacity=1)
        table.reserve_link(conn, 0)
        assert not table.is_link_available(conn, 0)
        table.release_link(conn, 0)
        assert table.is_link_available(conn, 0)

    def test_hops_no_longer_leak_into_the_link_snapshot(self) -> None:
        """The availability counter and the GUI snapshot stay separate."""
        table = ReservationTable()
        conn = Connection(zone_a="a", zone_b="b", max_link_capacity=1)
        table.reserve_link(conn, 0)
        assert not table.is_link_available(conn, 0)
        # No snapshot taken yet, so nothing is reported for the GUI.
        assert table.link_occupancy.get((conn.key, 0), 0) == 0


class TestTurnSnapshots:
    def _graph(self):
        return make_graph(
            drone_count=1,
            start=("start", (0, 0)),
            end=("goal", (2, 0)),
            zones=[{"name": "a", "coord": (1, 0)}],
            connections=[("start", "a"), ("a", "goal")],
        )

    def test_reports_live_zone_occupancy(self) -> None:
        graph = self._graph()
        table = ReservationTable()
        graph.get_zone_by_name("a").drone_count = 1

        table.record_turn(graph, 3)

        assert table.zone_occupancy[("a", 3)] == 1
        assert table.zone_occupancy[("start", 3)] == 0

    def test_combines_hops_and_in_flight_crossings(self) -> None:
        graph = self._graph()
        table = ReservationTable()
        conn = graph.get_connection("start", "a")
        table.reserve_link(conn, 0)
        conn.drone_count = 1  # a second drone is crossing the same link

        table.record_turn(graph, 0)

        assert table.link_occupancy[(conn.key, 0)] == 2

    def test_is_idempotent(self) -> None:
        graph = self._graph()
        table = ReservationTable()
        conn = graph.get_connection("start", "a")
        table.reserve_link(conn, 0)
        conn.drone_count = 1

        table.record_turn(graph, 0)
        table.record_turn(graph, 0)

        assert table.link_occupancy[(conn.key, 0)] == 2
