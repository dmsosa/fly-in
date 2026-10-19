from typing import cast

from model.graph import Zone, Connection


class ReservationTable:
    """Tracks zone and link capacity across turns.

    Zone occupancy is *persistent*: a drone keeps its slot from the turn
    it enters a zone until the turn it leaves, so ``zone.drone_count`` is
    always the live number of drones sitting there.

    Link usage is split in two:

    * ``connection.drone_count`` counts drones currently crossing a
      restricted link (they hold the link for the two turns of the
      crossing);
    * ``link_occupancy`` counts *instantaneous* hops made during a single
      turn, because a normal move finishes in the same turn and would
      otherwise leave no trace behind.
    """

    def __init__(self) -> None:
        """Initialize the per-turn occupancy ledgers."""
        self.zone_occupancy: dict[tuple[str, int], int] = {}
        self.link_occupancy: dict[tuple[tuple[str, str], int], int] = {}

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
        used = conn.drone_count + self.link_occupancy.get((conn.key, turn), 0)
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
        self.link_occupancy[key] = self.link_occupancy.get(key, 0) + 1

    def release_link(self, conn: Connection, turn: int) -> None:
        """Undo a single instantaneous hop on ``conn`` at ``turn``."""
        key = (conn.key, turn)
        if self.link_occupancy.get(key, 0) > 0:
            self.link_occupancy[key] -= 1
