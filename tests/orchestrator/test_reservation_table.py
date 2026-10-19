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
