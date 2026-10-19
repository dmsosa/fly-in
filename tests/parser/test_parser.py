"""Tests for :class:`parser.parser.FlyinParser`."""
from __future__ import annotations

from pathlib import Path

import pytest

from error import FlyinParseError
from model.graph import FlyinGraph
from parser import FlyinParser
from tests.helpers import write_map

VALID_MAP = """\
# a comment
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: a 1 0 [color=blue]
end_hub: goal 2 0 [color=red]
connection: start-a
connection: a-goal
"""


def parse(tmp_path: Path, text: str, name: str = "map"):
    return FlyinParser().parse(write_map(tmp_path, text, name))


class TestValidMaps:
    def test_happy_path(self, tmp_path: Path) -> None:
        data = parse(tmp_path, VALID_MAP)
        assert data["filename"] == "map"
        assert data["drone_count"] == 2
        assert data["start_zone"]["name"] == "start"
        assert data["start_zone"]["hub_type"] == "start"
        assert data["end_zone"]["name"] == "goal"
        assert data["end_zone"]["hub_type"] == "end"
        assert [zone["name"] for zone in data["zones"]] == ["a"]
        assert data["connections"][0] == {
            "zone_a": "start",
            "zone_b": "a",
            "max_link_capacity": 1,
        }

    def test_start_and_end_capacity_is_unbounded(
        self, tmp_path: Path
    ) -> None:
        text = (
            "nb_drones: 1\n"
            "start_hub: start 0 0 [max_drones=1]\n"
            "end_hub: goal 1 0 [max_drones=1]\n"
            "connection: start-goal\n"
        )
        data = parse(tmp_path, text)
        # The start/end hubs ignore any declared max_drones value: their
        # capacity is unbounded, modelled as ``None``.
        assert data["start_zone"]["max_drones"] is None
        assert data["end_zone"]["max_drones"] is None

    def test_filename_comes_from_the_path(self, tmp_path: Path) -> None:
        data = parse(tmp_path, VALID_MAP, name="my_level")
        assert data["filename"] == "my_level"


class TestInvalidMaps:
    def test_first_declaration_must_be_nb_drones(
        self, tmp_path: Path
    ) -> None:
        text = (
            "start_hub: start 0 0\n"
            "nb_drones: 1\n"
            "end_hub: goal 1 0\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)

    def test_empty_file(self, tmp_path: Path) -> None:
        with pytest.raises(FlyinParseError):
            parse(tmp_path, "")

    def test_duplicated_nb_drones(self, tmp_path: Path) -> None:
        text = (
            "nb_drones: 1\n"
            "nb_drones: 2\n"
            "start_hub: start 0 0\n"
            "end_hub: goal 1 0\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)

    def test_invalid_nb_drones_value(self, tmp_path: Path) -> None:
        text = (
            "nb_drones: abc\n"
            "start_hub: start 0 0\n"
            "end_hub: goal 1 0\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)

    def test_unknown_key(self, tmp_path: Path) -> None:
        text = (
            "nb_drones: 1\n"
            "start_hub: start 0 0\n"
            "end_hub: goal 1 0\n"
            "banana: yes\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)

    def test_line_without_colon(self, tmp_path: Path) -> None:
        text = (
            "nb_drones: 1\n"
            "this line has no colon\n"
            "start_hub: start 0 0\n"
            "end_hub: goal 1 0\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)

    def test_missing_start_hub(self, tmp_path: Path) -> None:
        text = (
            "nb_drones: 1\n"
            "end_hub: goal 1 0\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)

    def test_missing_end_hub(self, tmp_path: Path) -> None:
        text = (
            "nb_drones: 1\n"
            "start_hub: start 0 0\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)

    def test_duplicated_start_hub(self, tmp_path: Path) -> None:
        text = (
            "nb_drones: 1\n"
            "start_hub: start 0 0\n"
            "start_hub: start2 5 5\n"
            "end_hub: goal 1 0\n"
        )
        with pytest.raises(FlyinParseError):
            parse(tmp_path, text)


class TestParserToGraph:
    def test_parsed_dict_builds_a_graph(self, tmp_path: Path) -> None:
        graph = FlyinGraph(**parse(tmp_path, VALID_MAP))
        assert graph.drone_count == 2
        assert graph.get_zone_by_name("a") is not None
        assert graph.get_connection("start", "a") is not None
