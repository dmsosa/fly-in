"""Tests for :mod:`model.graph` (``Zone``, ``Connection``, ``FlyinGraph``)."""
from __future__ import annotations

import math

import pytest
from pydantic import ValidationError
from pydantic_core import PydanticCustomError

from model.graph import (
    Connection,
    FlyinGraph,
    HubType,
    Zone,
    ZoneType,
)
from tests.helpers import make_graph


class TestZoneDefaults:
    def test_defaults(self) -> None:
        zone = Zone(name="a", coord=(0, 0))
        assert zone.color is None
        assert zone.type is ZoneType.NORMAL
        assert zone.hub_type is HubType.HUB
        assert zone.max_drones == 1
        assert zone.drone_count == 0
        assert zone.connections == []
        assert zone.static_cost == 1

    def test_name_cannot_contain_dash_or_space(self) -> None:
        with pytest.raises(ValidationError):
            Zone(name="a-b", coord=(0, 0))
        with pytest.raises(ValidationError):
            Zone(name="a b", coord=(0, 0))

    def test_max_drones_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            Zone(name="a", coord=(0, 0), max_drones=0)


class TestZoneCosts:
    @pytest.mark.parametrize(
        ("zone_type", "expected"),
        [
            ("normal", 1),
            ("priority", 0.5),
            ("restricted", 2),
        ],
    )
    def test_static_cost_by_type(self, zone_type, expected) -> None:
        zone = Zone(name="a", coord=(0, 0), type=zone_type)
        assert zone.static_cost == expected

    def test_blocked_static_cost_is_infinite(self) -> None:
        zone = Zone(name="a", coord=(0, 0), type="blocked")
        assert math.isinf(zone.static_cost)

    def test_is_blocked_and_is_restricted(self) -> None:
        blocked = Zone(name="b", coord=(0, 0), type="blocked")
        restricted = Zone(name="r", coord=(1, 0), type="restricted")
        assert blocked.is_blocked() is True
        assert blocked.is_restricted() is False
        assert restricted.is_restricted() is True
        assert restricted.is_blocked() is False

    def test_is_occupied(self) -> None:
        zone = Zone(name="a", coord=(0, 0), max_drones=2)
        assert zone.is_occupied() is False
        zone.drone_count = 1
        assert zone.is_occupied() is False
        zone.drone_count = 2
        assert zone.is_occupied() is True

    def test_priority_is_cheaper_than_normal(self) -> None:
        normal = Zone(name="n", coord=(0, 0))
        priority = Zone(name="p", coord=(1, 0), type="priority")
        assert priority.get_dynamic_cost() < normal.get_dynamic_cost()

    def test_occupancy_raises_dynamic_cost(self) -> None:
        zone = Zone(name="a", coord=(0, 0), max_drones=1)
        empty_cost = zone.get_dynamic_cost()
        zone.drone_count = 1
        assert zone.get_dynamic_cost() > empty_cost


class TestZoneIdentity:
    def test_equality_and_hash_are_by_name(self) -> None:
        a1 = Zone(name="a", coord=(0, 0))
        a2 = Zone(name="a", coord=(9, 9))
        b = Zone(name="b", coord=(0, 0))
        assert a1 == a2
        assert hash(a1) == hash(a2)
        assert a1 != b
        assert {a1, a2, b} == {a1, b}


class TestConnection:
    def test_defaults(self) -> None:
        conn = Connection(zone_a="a", zone_b="b")
        assert conn.max_link_capacity == 1
        assert conn.drone_count == 0

    def test_self_connection_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Connection(zone_a="a", zone_b="a")

    def test_capacity_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            Connection(zone_a="a", zone_b="b", max_link_capacity=0)

    def test_key_is_canonical(self) -> None:
        assert Connection(zone_a="a", zone_b="b").key == ("a", "b")
        assert Connection(zone_a="b", zone_b="a").key == ("a", "b")

    def test_get_zone_names(self) -> None:
        assert Connection(
            zone_a="a", zone_b="b"
        ).get_zone_names() == ("a", "b")

    def test_get_opposite(self) -> None:
        conn = Connection(zone_a="a", zone_b="b")
        assert conn.get_opposite("a") == "b"
        assert conn.get_opposite("b") == "a"

    def test_get_opposite_unknown_raises(self) -> None:
        conn = Connection(zone_a="a", zone_b="b")
        with pytest.raises(PydanticCustomError):
            conn.get_opposite("c")


class TestFlyinGraph:
    def test_all_zones_contains_start_end_and_normal(
        self, linear_graph: FlyinGraph
    ) -> None:
        names = {zone.name for zone in linear_graph.all_zones}
        assert names == {"start", "goal", "a", "b"}
        assert len(linear_graph.all_zones) == 4

    def test_zone_lookup(self, linear_graph: FlyinGraph) -> None:
        assert (
            linear_graph.get_zone_by_name("start")
            is linear_graph.start_zone
        )
        assert linear_graph.get_zone_by_name("nope") is None

    def test_connections_are_linked_both_ways(
        self, linear_graph: FlyinGraph
    ) -> None:
        a = linear_graph.get_zone_by_name("a")
        assert len(a.connections) == 2
        assert {conn.get_opposite("a") for conn in a.connections} == {
            "start",
            "b",
        }

    def test_get_connection_is_order_independent(
        self, linear_graph: FlyinGraph
    ) -> None:
        forward = linear_graph.get_connection("start", "a")
        backward = linear_graph.get_connection("a", "start")
        assert forward is backward

    def test_get_connection_unknown_raises(
        self, linear_graph: FlyinGraph
    ) -> None:
        with pytest.raises(PydanticCustomError):
            linear_graph.get_connection("start", "b")

    def test_drone_count_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            make_graph(drone_count=0)

    def test_duplicate_zone_names_are_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_graph(
                zones=[{"name": "start", "coord": (2, 0)}],
            )

    def test_duplicate_zone_coords_are_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_graph(
                end=("goal", (1, 0)),
                zones=[{"name": "a", "coord": (0, 0)}],
            )

    def test_duplicate_connection_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make_graph(
                connections=[("start", "goal"), ("goal", "start")],
            )

    def test_connection_to_unknown_zone_is_a_clean_error(self) -> None:
        # A connection pointing at a zone that does not exist must be
        # reported as a validation error, not blow up while building
        # the zone -> connection links.
        with pytest.raises(ValidationError):
            FlyinGraph(
                filename="f",
                drone_count=1,
                start_zone=Zone(name="s", coord=(0, 0)),
                end_zone=Zone(name="e", coord=(1, 0)),
                connections=[Connection(zone_a="s", zone_b="zzz")],
            )
