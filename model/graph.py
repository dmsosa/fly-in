from enum import Enum
from functools import lru_cache
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError
from .constants import Coord
from .drone import Drone, DroneState

class HubType(Enum):
    HUB = "hub"
    START = "start"
    END = "end"


class ZoneType(Enum):
    NORMAL = "normal"
    PRIORITY = "priority"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class Zone(BaseModel):
    """
        Represents a Zone (vertex) inside the Network (graph)
        it can hold Drones, keep track of its possible connections
    """
    name: str = Field(pattern=r"^[^- ]*$")
    coord: Optional[Coord]
    color: Optional[str] = Field(default=None, pattern=r"^[^- ]*$")
    type: ZoneType = Field(default=ZoneType.NORMAL)
    hub_type: HubType = Field(default=HubType.HUB)
    max_drones: int = Field(default=1, gt=0)
    drone_count: int = Field(default=0, gt=0)
    drones_by_id: list[str] = Field(default_factory=list)
    connections: list[Coord] = Field(default_factory=list)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Zone):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def get_zone_cost(self) -> float:
        return float("inf")


class Connection(BaseModel):
    zone_a: str = Field(pattern=r"^[^- ]*$")
    zone_b: str = Field(pattern=r"^[^- ]*$")
    max_link_capacity: int = Field(default=1, gt=0)
    incoming: int = Field(default=0, ge=0)
    outgoing: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def not_circular_connection(self) -> "Connection":
        if self.zone_a == self.zone_b:
            raise PydanticCustomError(
                "self_connection",
                f"Invalid connection: {self.zone_a} and {self.zone_b} are the same hub."
                )
        return self

    @property
    def key(self) -> frozenset[Coord]:
        return frozenset((self.zone_a, self.zone_b))

    def get_opposite(self, zone_name: str) -> str:
        if zone_name == self.zone_a:
            return self.zone_b
        elif zone_name == self.zone_b:
            return self.zone_a
        else:
            raise PydanticCustomError(
                "connection_zone_not_exist",
                f"Zone name {zone_name} does not exist in this connection."
                )

    def get_zone_names(self) -> tuple[str, str]:
        return (self.zone_a, self.zone_b)


class FlyinGraph(BaseModel):
    """
    Graph of zones (vertices) and connections (edges).
    fields:
    drone_count # number of drones the graph contains
    start_zone # starting zone for all drones
    end_zone # goal zone for all drones
    zones # all zones in a set
    connections # all connections in a set
    """
    filename: str
    drone_count: int = Field(ge=1)
    start_zone: Zone
    end_zone: Zone
    zones: list[Zone] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    drones: dict[str, Drone] = Field(default_factory=dict)

    def get_zone_by_name(self, name: str) -> Zone | None:
        return self._zones_by_name.get(name)

    def get_zone_by_coord(self, name: str) -> Zone | None:
        return self._zones_by_name.get(name)

    # Model validation after -------------------------------------
    @model_validator(mode="after")
    def flyin_graph_validator(self) -> "FlyinGraph":
        """
        Checks:
        no duplicated zone names
        no duplicated zone coords
        no duplicated connections
        no self connections (already checked by Pydantic)
        no connection with zone that does not exist

        What's left to do after this:
        - all drones start at the start_zone
        - all drones know point to end_zone
        - all zones have a property which points to
        their links, it means, all the zones it is linked to
        via a Connection 
        """
        all_zones = self.zones + [self.start_zone, self.end_zone]
        all_zones_count = len(all_zones)

        unique_names = {z.name for z in all_zones}
        if  all_zones_count != len(unique_names):
            raise PydanticCustomError(
                "duplicate_hub_names",
                "Duplicated zone names, review your config file"
            )

        unique_coords = {z.coord for z in all_zones}
        if all_zones_count != len(unique_coords):
            raise PydanticCustomError(
                "duplicate_zone_coords",
                "Duplicated zone coordinates, review your config file"
            )

        unique_connections = set()
        for conn in self.connections:
            zone_a, zone_b = conn.get_zone_names()
            current_conn = tuple(sorted((zone_a, zone_b)))

            if current_conn in unique_connections:
                raise PydanticCustomError(
                    "duplicate_connection",
                    f"Duplicated connection, review your config file ({zone_a}, {zone_b})",
                )
            unique_connections.add(current_conn)

            if zone_a == zone_b:
                raise PydanticCustomError(
                    "self_connection",
                    f"Invalid connection: {zone_a} and {zone_b} are the same hub."
                )

            for z in [zone_a, zone_b]:
                if z not in unique_names:
                    raise PydanticCustomError(
                        "connection_zone_not_exist",
                        f"Zone name {z} does not exist in this connection."
                    )
    
        return self

    # ---- building ---------------------------------------------------
    def _create_drones(self) -> None:
        for i in range(0, self.drone_count):
            id = f"DS{(i + 1)}"
            d = Drone(
                    id=id,
                    state=DroneState.STOP,
                    start_zone=self.start_zone.name,
                    end_zone=self.end_zone.name,
                    current_zone=self.start_zone.name,
                    target=None,
                    move_count=0
                )
            self.drones[d.id] = d
            self.start_zone.drones_by_id.append(d.id)

    def _create_links(self) -> None:
        for conn in self.connections:
            zone_a_name, zone_b_name = conn.get_zone_names()
            zone_a = self.get_zone_by_name(zone_a_name)
            zone_b = self.get_zone_by_name(zone_b_name)
            zone_a.connections.append(conn)
            zone_b.connections.append(conn)

    def _build_indexes(self) -> None:
        all_zones = [self.start_zone, self.end_zone] + self.zones

        self._zones_by_name = {
            zone.name: zone
            for zone in all_zones
        }

        self._zones_by_coord = {
            zone.coord: zone
            for zone in all_zones
        }

    def init_graph(self) -> None:
        # Each drone needs to start in the start_hub
        # Each drone needs to have final goal end_hub
        self._build_indexes()
        self._create_drones()
        self._create_links()

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
        return self._zones_by_name.get(name)

    def get_zone_by_coord(self, coord: tuple[int, int]) -> Zone | None:
        """Linear lookup by (x, y); None if no zone is there."""
        return self._zones_by_coord.get(coord)


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
