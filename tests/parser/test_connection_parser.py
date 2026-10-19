"""Tests for :mod:`parser.connection_parser`."""
from __future__ import annotations

import pytest

from parser.connection_parser import (
    ConnectionParseError,
    ConnectionParser,
)


class TestValidConnections:
    def test_default_capacity(self) -> None:
        data = ConnectionParser.parse("a-b")
        assert data == {
            "zone_a": "a",
            "zone_b": "b",
            "max_link_capacity": 1,
        }

    def test_capacity_metadata(self) -> None:
        data = ConnectionParser.parse("a-b [max_link_capacity=3]")
        assert data["max_link_capacity"] == 3

    def test_capacity_without_brackets(self) -> None:
        data = ConnectionParser.parse("a-b max_link_capacity=2")
        assert data["max_link_capacity"] == 2


class TestInvalidConnections:
    def test_missing_dash(self) -> None:
        with pytest.raises(ConnectionParseError):
            ConnectionParser.parse("ab")

    def test_too_many_dashes(self) -> None:
        with pytest.raises(ConnectionParseError):
            ConnectionParser.parse("a-b-c")

    def test_unknown_metadata_key(self) -> None:
        with pytest.raises(ConnectionParseError):
            ConnectionParser.parse("a-b [foo=1]")

    def test_invalid_capacity(self) -> None:
        with pytest.raises(ConnectionParseError):
            ConnectionParser.parse("a-b [max_link_capacity=x]")

    def test_duplicated_capacity(self) -> None:
        with pytest.raises(ConnectionParseError):
            ConnectionParser.parse(
                "a-b [max_link_capacity=1 max_link_capacity=2]"
            )
