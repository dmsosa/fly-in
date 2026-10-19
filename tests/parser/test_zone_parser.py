"""Tests for :mod:`parser.zone_parser`."""
from __future__ import annotations

import pytest

from parser.zone_parser import ZoneParseError, ZoneParser


class TestValidZoneLines:
    def test_defaults(self) -> None:
        data = ZoneParser.parse("hub1 0 0")
        assert data == {
            "name": "hub1",
            "coord": (0, 0),
            "type": "normal",
            "color": None,
            "max_drones": 1,
        }

    def test_negative_coordinates(self) -> None:
        assert ZoneParser.parse("h -3 4")["coord"] == (-3, 4)

    def test_metadata_in_any_order(self) -> None:
        data = ZoneParser.parse(
            "h 1 2 [color=red max_drones=3 zone=restricted]"
        )
        assert data["color"] == "red"
        assert data["max_drones"] == 3
        assert data["type"] == "restricted"

    def test_brackets_are_optional(self) -> None:
        data = ZoneParser.parse("h 1 2 color=red")
        assert data["color"] == "red"


class TestInvalidZoneLines:
    def test_too_few_tokens(self) -> None:
        with pytest.raises(ZoneParseError):
            ZoneParser.parse("h 0")

    def test_non_integer_coordinates(self) -> None:
        with pytest.raises(ZoneParseError):
            ZoneParser.parse("h x 0")

    def test_unknown_metadata_key(self) -> None:
        with pytest.raises(ZoneParseError):
            ZoneParser.parse("h 0 0 [foo=bar]")

    def test_duplicated_metadata_key(self) -> None:
        with pytest.raises(ZoneParseError):
            ZoneParser.parse("h 0 0 [max_drones=1 max_drones=2]")

    def test_invalid_max_drones_value(self) -> None:
        with pytest.raises(ZoneParseError):
            ZoneParser.parse("h 0 0 [max_drones=abc]")

    def test_metadata_token_without_equals(self) -> None:
        with pytest.raises(ZoneParseError):
            ZoneParser.parse("h 0 0 [max_drones]")
