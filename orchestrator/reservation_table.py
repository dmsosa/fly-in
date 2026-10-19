from typing import cast

from model.graph import FlyinGraph, Zone, Connection


class ReservationTable:
    """Tracks zone and link capacity across turns.

    Zone occupancy is *persistent*: a drone keeps its slot from the turn
    it enters a zone until the turn it leaves, so ``zone.drone_count`` is
    always the live number of drones sitting there.

    Link usage is split in two:

    * ``connection.drone_count`` counts drones currently crossing a
      restricted link (they hold the link for the two turns of the
      crossing);
    * ``_link_hops`` counts *instantaneous* normal hops made during a
      single turn, because a normal move finishes in the same turn and
      would otherwise leave no trace behind.

    ``zone_occupancy`` and ``link_occupancy`` are per-turn *snapshots*
    produced by :meth:`record_turn`. They are what the terminal GUI reads
    to display usage; recomputing them from the live counters keeps them
    accurate even for drones that simply stay in a zone.
    """

    def __init__(self) -> None:
        """Initialize the per-turn occupancy ledgers."""
        self.zone_occupancy: dict[tuple[str, int], int] = {}
        self.link_occupancy: dict[tuple[tuple[str, str], int], int] = {}
        self._link_hops: dict[tuple[tuple[str, str], int], int] = {}

    def is_zone_available(
        self,
        zone: Zone,
        turn: int,
        is_start_or_end: bool,
    ) -> bool:
        """Return ``True`` when ``zone`` has a free slot at ``turn``.

        Args:
            zone: Target zone.
            turn: Target simulation turn.
            is_start_or_end: True for the start/end hubs, whose capacity
                is unbounded.
        """
        if is_start_or_end or zone.is_unlimited_capacity():
            return True
        return zone.drone_count < cast(int, zone.max_drones)

    def is_link_available(self, conn: Connection, turn: int) -> bool:
        """Return ``True`` when ``conn`` can carry one more drone.

        Args:
            conn: Traversed connection.
            turn: Traversal turn.
        """
        used = conn.drone_count + self._link_hops.get((conn.key, turn), 0)
        return used < conn.max_link_capacity

    def reserve_zone(self, zone: Zone, turn: int) -> None:
        """Register a drone entering ``zone`` at ``turn``."""
        zone.drone_count += 1
        key = (zone.name, turn)
        self.zone_occupancy[key] = self.zone_occupancy.get(key, 0) + 1

    def release_zone(self, zone: Zone, turn: int) -> None:
        """Register a drone leaving ``zone`` at ``turn``."""
        if zone.drone_count > 0:
            zone.drone_count -= 1
        key = (zone.name, turn)
        if self.zone_occupancy.get(key, 0) > 0:
            self.zone_occupancy[key] -= 1

    def reserve_link(self, conn: Connection, turn: int) -> None:
        """Register one instantaneous hop on ``conn`` at ``turn``."""
        key = (conn.key, turn)
        self._link_hops[key] = self._link_hops.get(key, 0) + 1

    def release_link(self, conn: Connection, turn: int) -> None:
        """Undo a single instantaneous hop on ``conn`` at ``turn``."""
        key = (conn.key, turn)
        if self._link_hops.get(key, 0) > 0:
            self._link_hops[key] -= 1

    def record_turn(self, graph: FlyinGraph, turn: int) -> None:
        """Snapshot the live occupancy of ``turn`` for the GUI / reporting.

        Zone usage is the number of drones sitting in each zone, and link
        usage is the normal hops of the turn plus the drones still crossing
        a restricted link. Both are recomputed from the live counters, so
        calling this again for the same turn is idempotent.

        Args:
            graph: Graph the simulation is running on.
            turn: Turn that was just simulated.
        """
        for zone in graph.all_zones:
            self.zone_occupancy[(zone.name, turn)] = zone.drone_count
        for conn in graph.connections:
            hops = self._link_hops.get((conn.key, turn), 0)
            self.link_occupancy[(conn.key, turn)] = hops + conn.drone_count
