"""Reusable builders shared by the test modules.

Everything here goes through the public models so that the tests stay
focused on behaviour instead of pydantic plumbing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Union

from model.drone import Drone
from model.graph import Connection, FlyinGraph, Zone

Coord = tuple[int, int]
ZoneSpec = Union[Zone, dict[str, Any]]
ConnSpec = Union[Connection, dict[str, Any], tuple[str, str]]


def make_graph(
    *,
    drone_count: int = 1,
    start: tuple[str, Coord] = ("start", (0, 0)),
    end: tuple[str, Coord] = ("goal", (9, 9)),
    zones: Iterable[ZoneSpec] = (),
    connections: Iterable[ConnSpec] = (),
    start_max_drones: int = 1,
    end_max_drones: int = 1,
) -> FlyinGraph:
    """Build a :class:`FlyinGraph` from compact specs.

    Args:
        drone_count: number of drones that start on the graph.
        start: ``(name, coord)`` of the start hub.
        end: ``(name, coord)`` of the end hub.
        zones: ``Zone`` instances or ``Zone`` kwargs dicts.
        connections: ``Connection`` instances, kwargs dicts or
            ``(zone_a, zone_b)`` tuples.
        start_max_drones: capacity of the generated start hub.
        end_max_drones: capacity of the generated end hub. Raise it when a
            test needs more than one drone to be delivered.

    Returns:
        A fully built ``FlyinGraph`` (links + indexes already created).
    """
    start_zone = Zone(
        name=start[0],
        coord=start[1],
        hub_type="start",
        max_drones=start_max_drones,
    )
    end_zone = Zone(
        name=end[0],
        coord=end[1],
        hub_type="end",
        max_drones=end_max_drones,
    )

    zone_models: list[Zone] = [
        zone if isinstance(zone, Zone) else Zone(**zone) for zone in zones
    ]

    conn_models: list[Connection] = []
    for conn in connections:
        if isinstance(conn, Connection):
            conn_models.append(conn)
        elif isinstance(conn, dict):
            conn_models.append(Connection(**conn))
        else:
            zone_a, zone_b = conn
            conn_models.append(
                Connection(zone_a=zone_a, zone_b=zone_b)
            )

    return FlyinGraph(
        filename="test_map",
        drone_count=drone_count,
        start_zone=start_zone,
        end_zone=end_zone,
        zones=zone_models,
        connections=conn_models,
    )


def write_map(tmp_path: Path, text: str, name: str = "map") -> Path:
    """Write ``text`` to ``<tmp_path>/<name>.txt`` and return the path."""
    path = tmp_path / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def make_drone(
    graph: FlyinGraph,
    zone_name: str,
    drone_id: str = "D1",
    occupy: bool = True,
) -> Drone:
    """Create a drone sitting in ``zone_name``.

    When ``occupy`` is true the zone keeps track of the drone, which is
    what the simulation relies on before a move happens.
    """
    zone = graph.get_zone_by_name(zone_name)
    if zone is None:
        raise AssertionError(f"unknown zone in test graph: {zone_name}")
    drone = Drone(
        id=drone_id,
        start_zone=graph.start_zone,
        end_zone=graph.end_zone,
        current_zone=zone,
    )
    if occupy:
        zone.drone_count += 1
        zone.drones_by_id.append(drone.id)
    return drone


def make_orchestrator(
    graph: FlyinGraph,
    output_file: str = "output.txt",
):
    """Wire a graph + Dijkstra pathfinding into an ``Orchestrator``.

    Imported lazily so that test modules which only need the graph
    builders do not pull the simulation into their import path.
    """
    from orchestrator.orchestrator import Orchestrator
    from pathfinding.dijkstra import DijkstraPathfinding

    return Orchestrator(
        graph=graph,
        pathfinding=DijkstraPathfinding(graph),
        output_file=output_file,
    )
