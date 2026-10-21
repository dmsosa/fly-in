from enum import Enum
import math
import re
from typing import Any, Optional
from pydantic import BaseModel, \
                Field, \
                field_validator, \
                model_validator
from pydantic_core import PydanticCustomError
from .constants import Coord


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
    name: str
    coord: Coord
    color: Optional[str] = Field(default=None)
    type: ZoneType = Field(default=ZoneType.NORMAL)
    hub_type: HubType = Field(default=HubType.HUB)
    max_drones: Optional[int] = Field(default=1, gt=0)
    drone_count: int = Field(default=0, ge=0)
    static_cost: int = Field(default=1)
    connections: list[Any] = Field(default_factory=list)
    drones_by_id: list[str] = Field(default_factory=list)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Zone):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    @field_validator('name')
    @classmethod
    def name_no_dashes_or_spaces(cls, value: str) -> str:
        if not re.match(r"^[^- ]*$", value):
            raise ValueError(
                f"Zone name must not contain dashes or spaces: '{value}'"
                )
        return value

    def model_post_init(self, context) -> None:
        if self.type == ZoneType.NORMAL:
            self.static_cost = 1
        elif self.type == ZoneType.PRIORITY:
            self.static_cost = 0.5
        elif self.type == ZoneType.RESTRICTED:
            self.static_cost = 2
        elif self.type == ZoneType.BLOCKED:
            self.static_cost = math.inf

    def is_blocked(self) -> bool:
        return self.type == ZoneType.BLOCKED

    def is_restricted(self) -> bool:
        return self.type == ZoneType.RESTRICTED

    def is_occupied(self) -> bool:
        if self.max_drones is None:
            return False
        return self.drone_count >= self.max_drones

    def get_dynamic_cost(self) -> float:
        """
        Cost of *being* in this zone.

        It mixes the zone preference (priority < normal < restricted) with
        an occupancy penalty, so the value always grows as the zone fills
        up. Blocked zones are infinitely expensive.
        """
        type_weight = {
            ZoneType.NORMAL: 1.0,
            ZoneType.PRIORITY: 0.5,
            ZoneType.RESTRICTED: 2.0,
            ZoneType.BLOCKED: math.inf,
        }[self.type]
        capacity = self.max_drones if self.max_drones is not None else 1
        occupancy = self.drone_count / max(capacity, 1)
        return type_weight * (1 + occupancy)

    def get_cost(self) -> float:
        return self.get_dynamic_cost()

    def is_unlimited_capacity(self) -> bool:
        """Check whether the zone has unbounded drone capacity.

        Returns:
            bool: True when ``max_drones`` is ``None`` (start/end hubs).
        """
        return self.max_drones is None


class Connection(BaseModel):
    zone_a: str
    zone_b: str
    max_link_capacity: int = Field(default=1, gt=0)
    drone_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def not_circular_connection(self) -> "Connection":
        if self.zone_a == self.zone_b:
            raise PydanticCustomError(
                "self_connection",
                f"Invalid connection: {self.zone_a} and \
                {self.zone_b} are the same hub."
                )
        return self

    @property
    def key(self) -> tuple[str, str]:
        """Canonical (sorted) pair — (B,A) and (A,B) both → (A,B)."""
        return tuple(sorted((self.zone_a, self.zone_b)))

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
    drone_count: int = Field(gt=0, lt=101)
    start_zone: Zone
    end_zone: Zone
    zones: list[Zone] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    all_zones: list[Zone] = Field(default_factory=list)
    adjacency_list: dict[
        str,
        list[tuple[str, int]]
        ] = Field(default_factory=dict)

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
        self.all_zones = self.zones + [self.start_zone, self.end_zone]
        all_zones_count = len(self.all_zones)

        unique_names = {z.name for z in self.all_zones}
        if all_zones_count != len(unique_names):
            all_zones_len = len(self.all_zones)
            found = False
            for i in range(0, all_zones_len):
                zone_i = self.all_zones[i]
                first_dup = zone_i.name
                for j in range(i + 1, all_zones_len):
                    zone_j = self.all_zones[j]
                    second_dup = zone_j.name
                    if first_dup == second_dup:
                        found = True
                        break
                if found:
                    break

            raise PydanticCustomError(
                "duplicate_hub_names",
                f"Duplicated zone names {first_dup} - {second_dup}"
            )

        unique_coords = {z.coord for z in self.all_zones}
        if all_zones_count != len(unique_coords):
            all_zones_len = len(self.all_zones)
            found = False
            for i in range(0, all_zones_len):
                zone_i = self.all_zones[i]
                first_dup = zone_i.coord
                for j in range(i + 1, all_zones_len):
                    zone_j = self.all_zones[j]
                    second_dup = zone_j.coord
                    if first_dup == second_dup:
                        found = True
                        break
                if found:
                    break
            raise PydanticCustomError(
                "duplicate_zone_coords",
                f"Duplicated zone coordinates {first_dup} - {second_dup}"
            )

        unique_connections = set()
        for conn in self.connections:
            zone_a, zone_b = conn.get_zone_names()
            current_conn = tuple(sorted((zone_a, zone_b)))

            if current_conn in unique_connections:
                raise PydanticCustomError(
                    "duplicate_connection",
                    f"Duplicated zone connection {zone_a} - {zone_b}"
                )
            unique_connections.add(current_conn)

            if zone_a == zone_b:
                raise PydanticCustomError(
                    "self_connection",
                    f"Invalid connection: {zone_a} and {zone_b} \
                    are the same hub."
                )

            for z in [zone_a, zone_b]:
                if z not in unique_names:
                    raise PydanticCustomError(
                        "zone_name_in_connection_not_exist",
                        f"Zone name {z} does not exist. \
                        Failed to create connection."
                    )

        self._build_indexes()

        return self

    # ---- building ---------------------------------------------------
    def _build_indexes(self) -> None:
        all_zones = [self.start_zone, self.end_zone] + self.zones

        self._zones_by_name = {
            zone.name: zone
            for zone in all_zones
        }

        self._conn_index = {c.key: c for c in self.connections}

        # Give every zone its incident connections. Rebuilt from scratch so
        # that re-validating a graph never duplicates the links.
        for zone in self._zones_by_name.values():
            zone.connections = []
        for conn in self.connections:
            self._zones_by_name[conn.zone_a].connections.append(conn)
            self._zones_by_name[conn.zone_b].connections.append(conn)

    def _build_adjacency_list(self) -> None:
        adj_lst = {}
        for conn in self.connections:
            zone_a = self.get_zone_by_name(conn.zone_a)
            zone_b = self.get_zone_by_name(conn.zone_b)
            if zone_a.name not in adj_lst:
                adj_lst[zone_a.name] = []
            if zone_b.name not in adj_lst:
                adj_lst[zone_b.name] = []
            adj_lst[conn.zone_a].append((conn.zone_b, zone_b.static_cost))
            adj_lst[conn.zone_b].append((conn.zone_a, zone_a.static_cost))

        self.adjacency_list = adj_lst

    # ---- lookups ----------------------------------------------------
    def get_zone_by_name(self, name: str) -> Zone | None:
        """O(1) lookup by name."""
        return self._zones_by_name.get(name)

    def get_connection(self, zone_a: str, zone_b: str) -> Connection:
        conn = self._conn_index.get(tuple(sorted((zone_a, zone_b))))
        if conn is None:
            raise PydanticCustomError(
                "connection_not_found",
                f"No connection found between '{zone_a}' and '{zone_b}'.",
            )
        return conn

    def get_neighbors(self, zone_name: str) -> list[Zone]:
        """
        Retrieves all accessible adjacent zones that are not blocked.

        Args:
            zone: The Zone object to check neighbors from.

        Returns:
            A list of accessible Zone objects connected to the input zone.
            Zones of type 'blocked' are excluded.
        """
        neighbors = []
        for connection in self.connections:
            if connection.zone_a == zone_name:
                neighbor = self.get_zone_by_name(connection.zone_b)
                if neighbor.type != ZoneType.BLOCKED:
                    neighbors.append(neighbor)
            elif connection.zone_b == zone_name:
                neighbor = self.get_zone_by_name(connection.zone_a)
                if neighbor.type != ZoneType.BLOCKED:
                    neighbors.append(neighbor)
        return neighbors
