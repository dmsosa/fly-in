"""Integration tests: every shipped map must be fully delivered.

These exercise the whole pipeline (parser -> models -> pathfinding ->
orchestrator) exactly like ``main.py`` does, so a regression anywhere in
the stack shows up here.

The test is parametrized over the map files, so dropping a new ``.txt``
into ``maps/`` automatically adds it to the suite.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from model.drone import DroneState
from model.graph import FlyinGraph
from orchestrator.orchestrator import Orchestrator
from parser import FlyinParser
from pathfinding import DijkstraPathfinding

MAPS = Path(__file__).resolve().parents[1] / "maps"
MAP_FILES = sorted(MAPS.glob("*/*.txt"))

# A correct schedule finishes every shipped map well under this ceiling;
# hitting it means the fleet is oscillating instead of progressing.
TURN_CEILING = 1000


def test_at_least_one_map_is_shipped() -> None:
    assert MAP_FILES, f"no maps found under {MAPS}"


@pytest.mark.parametrize(
    "map_path", MAP_FILES, ids=[f"{p.parent.name}/{p.name}" for p in MAP_FILES]
)
def test_map_is_completely_solved(map_path: Path, tmp_path: Path) -> None:
    graph = FlyinGraph(**FlyinParser().parse(str(map_path)))
    orch = Orchestrator(
        graph=graph,
        pathfinding=DijkstraPathfinding(graph),
        output_file=str(tmp_path / "output.txt"),
    )

    history = orch.run_orchestra()

    # Every drone delivered...
    assert orch.drones, "the map should spawn at least one drone"
    assert all(
        drone.state is DroneState.DELIVERED
        for drone in orch.drones.values()
    ), f"{map_path.name}: some drones never arrived"

    # ...in a bounded number of turns...
    assert orch.turn_count == len(history)
    assert 0 < orch.turn_count < TURN_CEILING

    # ...and nothing is left occupying a link.
    assert all(conn.drone_count == 0 for conn in graph.connections)

    # The export is one non-empty line per turn of ``D<id>-<zone>`` moves.
    orch.export_turns()
    lines = (tmp_path / "output.txt").read_text(encoding="utf-8").splitlines()
    assert len(lines) == orch.turn_count
    for line in lines:
        assert line, "a turn must never be an empty line"
        for move in line.split(" "):
            parts = move.split("-")
            assert parts[0].startswith("D") and parts[0][1:].isdigit()
            # 2 tokens: a landed move; 3 tokens: an in-flight crossing.
            assert len(parts) in (2, 3)
