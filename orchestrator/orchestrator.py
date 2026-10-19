import sys
from typing import Any, Optional

from error.error import FlyinError
from model.drone import Drone, DroneState
from model.graph import Connection, FlyinGraph, HubType, Zone
from orchestrator.reservation_table import ReservationTable
from pathfinding import DijkstraPathfinding


class Move:
    """
    A single drone instruction for one turn.

    ``D<ID>-<zone>`` for a normal arrival, ``D<ID>-<origin>-<dest>`` while
    a restricted connection is being crossed.
    """

    def __init__(self, turn_id: int, drone_id: str, target_name: str) -> None:
        self.turn_id = turn_id
        self.drone_id = drone_id
        self.target_name = target_name

    def to_str(self) -> str:
        return f"{self.drone_id}-{self.target_name}"


class Orchestrator:
    def __init__(
        self,
        graph: FlyinGraph,
        pathfinding: DijkstraPathfinding,
        output_file: str = "output.txt",
    ) -> None:
        self.graph = graph
        self.pathfinding = pathfinding
        self.turn_count = 0
        self.history: list[list[Move]] = []
        self.output_file = output_file
        self.drones: dict[str, Drone] = {}
        self.reservation_table = ReservationTable()
        self._init_metrics()
        self._create_drones()

    # ---- setup ------------------------------------------------------
    def _create_drones(self) -> None:
        if self.graph is None:
            raise FlyinError("Graph is not defined")

        start = self.graph.start_zone
        for i in range(self.graph.drone_count):
            drone_id = f"D{i + 1}"
            drone = Drone(
                id=drone_id,
                state=DroneState.STOP,
                current_zone=start,
                target=None,
            )
            # The drone remembers where it started so it does not
            # immediately turn around on the very first move.
            drone.add_last_visited(start.name)
            self.drones[drone_id] = drone
            start.drone_count += 1
            start.drones_by_id.append(drone_id)

    def _init_metrics(self) -> None:
        self.metrics: dict[str, Any] = {
            "turn_count": 0,
            "drones_moved_per_turn": 0,
            "min_turn_drone": 0,
            "max_turn_drone": 0,
            "avg_turn_drone": 0,
            "total_path_cost": 0,
        }

    def get_drone_by_id(self, name: str) -> Optional[Drone]:
        """O(1) lookup by drone id."""
        return self.drones.get(name)

    # ---- simulation -------------------------------------------------
    def run_orchestra(self) -> list[list[Move]]:
        history: list[list[Move]] = []
        # Hard ceiling: a correct schedule delivers every drone well before
        # this, so hitting it means the fleet is oscillating/deadlocked.
        max_turns = (
            4 * max(1, len(self.graph.all_zones))
            * max(1, len(self.drones))
            + 50
        )

        while self._continue():
            if self.turn_count >= max_turns:
                raise FlyinError(
                    f"No progress after {max_turns} turns: deadlock detected."
                )
            moves = self.next_turn()
            if not moves:
                # Nobody moved and nothing is in flight: the fleet can
                # never make progress again, so fail fast instead of
                # spinning until the turn ceiling.
                raise FlyinError("Deadlock detected: every drone is waiting.")
            self.turn_count += 1
            history.append(moves)

        self.history = history
        self._get_metrics()
        return history

    def next_turn(self) -> list[Move]:
        """
        Advance the simulation one turn.

        Drones already crossing a restricted link land first, then every
        stopped drone picks the cheapest neighbour that still moves it
        strictly closer to the goal. Waiting is the last resort.
        """
        turn = self.turn_count
        moves: list[Move] = []
        finished_flyin: set[str] = set()

        # Phase 1: land drones that finished a restricted crossing.
        for drone in self.drones.values():
            if drone.state != DroneState.FLYIN:
                continue

            target = drone.target
            if target is None:
                drone.state = DroneState.STOP
                continue

            drone.wait_count += 1
            # A restricted zone costs 2 turns: one to ride the link, one
            # to actually enter the zone.
            if drone.wait_count < target.static_cost - 1:
                continue

            if not self.reservation_table.is_zone_available(
                target, turn, target.hub_type == HubType.END
            ):
                # The zone filled up while the drone was in flight; keep
                # holding the link and try again next turn.
                continue

            connection = drone.connection
            if connection is not None and connection.drone_count > 0:
                connection.drone_count -= 1
            self._land(drone, target, turn)
            finished_flyin.add(drone.id)
            moves.append(Move(turn, drone.id, target.name))

        # Phase 2: stopped drones choose their cheapest legal neighbour.
        for drone in self.drones.values():
            if drone.id in finished_flyin:
                continue
            if drone.state in (DroneState.DELIVERED, DroneState.FLYIN):
                continue

            current = drone.current_zone
            if current is None:
                # Defensive: an in-flight drone without a target is stuck.
                drone.state = DroneState.WAIT
                continue

            chosen, connection = self._choose_next(drone, current, turn)
            if chosen is None or connection is None:
                drone.state = DroneState.WAIT
                continue

            # The drone always gives its slot back to the zone it leaves.
            self.reservation_table.release_zone(current, turn)

            if chosen.is_restricted():
                # A restricted crossing holds the link for two turns, so it
                # is tracked by ``connection.drone_count`` and must NOT also
                # be added to the per-turn hop ledger (that would count the
                # same drone twice and block the link).
                drone.current_zone = None
                drone.target = chosen
                drone.connection = connection
                drone.wait_count = 0
                connection.drone_count += 1
                drone.state = DroneState.FLYIN
                target_name = f"{current.name}-{chosen.name}"
            else:
                # A normal hop is instantaneous, so it only lives in the
                # per-turn ledger.
                self.reservation_table.reserve_link(connection, turn)
                self._land(drone, chosen, turn)
                target_name = chosen.name

            moves.append(Move(turn, drone.id, target_name))

        # Snapshot the live usage of this turn for the GUI / reporting.
        self.reservation_table.record_turn(self.graph, turn)
        return moves

    def _choose_next(
        self, drone: Drone, current: Zone, turn: int
    ) -> tuple[Optional[Zone], Optional[Connection]]:
        """
        Pick the best neighbour for ``drone``.

        Candidates must move the drone strictly closer to the goal, which
        is what makes the greedy schedule ping-pong free: the
        ``distance_map`` decreases on every accepted move, so a drone can
        never bounce between two zones. Among those candidates the drone
        prefers a zone it has not visited recently (``last_visited``) and
        falls back to the closest one otherwise.
        """
        distance_map = self.pathfinding.distance_map
        current_distance = distance_map.get(current.name, float("inf"))

        # Every accepted candidate must lower the cost-to-go *strictly*.
        # Equal-distance moves are rejected on purpose: waiting for the
        # cheapest option to free up is always better than drifting onto a
        # branch that does not bring the drone any closer.
        best_distance = float("inf")
        candidates: list[tuple[Zone, Connection]] = []
        for candidate in self.pathfinding.find_best_zones(current):
            if candidate.name == current.name:
                continue
            candidate_distance = distance_map.get(
                candidate.name, float("inf")
            )
            if not candidate_distance < current_distance:
                continue
            if not self.reservation_table.is_zone_available(
                candidate, turn, candidate.hub_type == HubType.END
            ):
                continue
            connection = self.graph.get_connection(
                current.name, candidate.name
            )
            if not self.reservation_table.is_link_available(connection, turn):
                continue

            if candidate_distance < best_distance:
                best_distance = candidate_distance
                candidates = [(candidate, connection)]
            elif candidate_distance == best_distance:
                candidates.append((candidate, connection))

        if not candidates:
            return None, None

        # ``last_visited`` is a *preference* among the equally-good
        # candidates, never a hard ban, so the drone is never stranded just
        # because it already knows every option.
        for candidate, connection in candidates:
            if not drone.has_visited(candidate.name):
                return candidate, connection
        return candidates[0]

    def _land(self, drone: Drone, zone: Zone, turn: int) -> None:
        """Move ``drone`` into ``zone`` and update all bookkeeping."""
        self.reservation_table.reserve_zone(zone, turn)
        drone.current_zone = zone
        drone.target = None
        drone.connection = None
        drone.wait_count = 0
        drone.move_count += 1
        drone.add_last_visited(zone.name)
        drone.state = (
            DroneState.DELIVERED
            if zone.hub_type == HubType.END
            else DroneState.STOP
        )

    def _continue(self) -> bool:
        return not all(
            drone.state == DroneState.DELIVERED
            for drone in self.drones.values()
        )

    # ---- reporting --------------------------------------------------
    def _get_metrics(self) -> None:
        """Compute and store final performance metrics after a run."""
        self.metrics["turn_count"] = self.turn_count

        path_costs = [d.move_count for d in self.drones.values()]
        self.metrics["total_path_cost"] = sum(path_costs)

        if self.turn_count > 0:
            self.metrics["drones_moved_per_turn"] = (
                self.metrics["total_path_cost"]
                / (self.turn_count * self.graph.drone_count)
                * 100
            )
        else:
            self.metrics["drones_moved_per_turn"] = 0

        delivered = [
            d for d in self.drones.values()
            if d.state == DroneState.DELIVERED
        ]
        if delivered:
            costs = [d.move_count for d in delivered]
            self.metrics["min_turn_drone"] = min(costs)
            self.metrics["max_turn_drone"] = max(costs)
            self.metrics["avg_turn_drone"] = sum(costs) / len(costs)

    def export_turns(self) -> None:
        if not self.history:
            raise FlyinError(
                "Tried to export turns without running simulation"
            )

        lines = [
            " ".join(move.to_str() for move in turn)
            for turn in self.history
        ]
        output = "\n".join(lines)

        try:
            with open(self.output_file, "w") as f:
                f.write(output)
        except (IOError, PermissionError) as e:
            print(
                f"Error while writing turn output to file:\n{e}",
                file=sys.stderr,
            )
