"""The drone network: zones, connections and an adjacency list."""
from pydantic import BaseModel, Field

from .connection import Connection
from .zone import Zone


class FlyinGraph:
    """Graph of zones (vertices) and connections (edges)."""

    def __init__(self, drone_count: int = 0) -> None:
        """Create an empty graph for `drone_count` drones."""
        if drone_count < 0:
            raise ValueError("drone_count cannot be negative")
        self.drone_count = drone_count
        self.zones: set[Zone] = set()
        self.connections: set[Connection] = set()
        self.graph: dict[Zone, set[Connection]] = {}
        self.zone_by_name: dict[str, Zone] = {}
        self._start: Zone | None = None
        self._end: Zone | None = None

    # ---- building ---------------------------------------------------
    def add_zone(self, zone: Zone) -> None:
        """Add a zone.

        Raises:
            ValueError: duplicated name, or second start/end zone.
        """
        if zone.name in self.zone_by_name:
            raise ValueError(f"Duplicated zone name: '{zone.name}'")
        if zone.is_start:
            if self._start is not None:
                raise ValueError("There must be exactly one start_hub")
            self._start = zone
            zone.drone_count = self.drone_count
        if zone.is_end:
            if self._end is not None:
                raise ValueError("There must be exactly one end_hub")
            self._end = zone
        self.zones.add(zone)
        self.zone_by_name[zone.name] = zone
        self.graph[zone] = set()

    def add_connection(self, connection: Connection) -> None:
        """Add a connection between two already-added zones.

        Raises:
            ValueError: unknown zone or duplicated connection.
        """
        for zone in (connection.origin, connection.destination):
            if zone.name not in self._by_name:
                raise ValueError(f"Unknown zone: '{zone.name}'")
        if connection in self.connections:
            raise ValueError(f"Duplicated connection: {connection.name}")
        self.connections.add(connection)
        self.graph[connection.origin].add(connection)
        self.graph[connection.destination].add(connection)

    # ---- lookups ----------------------------------------------------
    @property
    def start_zone(self) -> Zone:
        """The unique start zone."""
        if self._start is None:
            raise ValueError("No start_hub defined")
        return self._start

    @property
    def end_zone(self) -> Zone:
        """The unique end zone."""
        if self._end is None:
            raise ValueError("No end_hub defined")
        return self._end

    def get_zone_by_name(self, name: str) -> Zone | None:
        """O(1) lookup by name."""
        return self._by_name.get(name)

    def get_zone_by_coord(self, coord: tuple[int, int]) -> Zone | None:
        """Linear lookup by (x, y); None if no zone is there."""
        for zone in self.zones:
            if zone.coord == coord:
                return zone
        return None

    def get_connections_for_zone(self, zone: Zone) -> set[Connection]:
        """Connections touching `zone` (empty set if unknown)."""
        return self.graph.get(zone, set())

    def get_connections_for_coord(
        self, coord: tuple[int, int]
    ) -> set[Connection]:
        """Connections touching the zone located at `coord`."""
        zone = self.get_zone_by_coord(coord)
        return self.get_connections_for_zone(zone) if zone else set()

    def get_connection_by_coord(
        self, a: tuple[int, int], b: tuple[int, int]
    ) -> Connection | None:
        """Connection between the zones at `a` and `b`, in any order."""
        for conn in self.connections:
            if {conn.origin.coord, conn.destination.coord} == {a, b}:
                return conn
        return None

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        """Adjacent zones a drone may enter (blocked ones excluded)."""
        return [
            conn.other_end(zone)
            for conn in self.get_connections_for_zone(zone)
            if not conn.other_end(zone).is_blocked
        ]