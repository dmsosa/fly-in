import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from model.drone import DroneState
from model.drone import Drone
from model.graph import FlyinGraph


class Orchestrator(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    turn_count: int = Field(ge=0)
    graph: FlyinGraph
    drones: dict[str, Drone] = Field(default_factory=dict)
    drones_moving: list[Drone] = Field(default_factory=list)
    drones_finished: list[Drone] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    def _create_drones(self) -> None:
        for i in range(0, self.graph.drone_count):
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
        
    def model_post_init(self, __context) -> None:
        self.metrics = {
            "turn_count": 0,
            "drone_move_count": 0,
            "drones_moved_per_turn": 0,
            "min_turn_drone": 0,
            "max_turn_drone": 0,
            "avg_turn_drone": 0,
            "min_move_drone": 0,
            "max_move_drone": 0,
            "avg_move_drone": 0,
            "total_path_cost": 0,
        }
        self._create_drones()

    def _turn_to_str(self) -> None:
        turn_str = ""
        moves = []
        for drone in self.drones_moving:
            if drone.state is DroneState.FLYIN:
                dest = drone.dest if drone.dest else 'Unknown'
                drone_str = f"{drone.id}-{dest}"
            elif drone.state is DroneState.WAIT:
                origin = drone.origin if drone.origin else 'Unknown'
                dest = drone.dest if drone.dest else 'Unknown'
                drone_str = f"{drone.id}-{origin}-{dest}"
            moves.append(drone_str)

        turn_str = " ".join(moves)
        return turn_str

    def _output_move(self, turn_str: str) -> None:
        print(f"Orchestrator producing output move: {turn_str}", file=sys.stderr)

        try:
            with open("output.txt", "a") as f:
                f.write(turn_str + "\n")
        except (IOError, PermissionError) as e:
            print(f"Error while writing turn output to file:\n{e}", file=sys.stderr)

    def _get_metrics(self) -> None:
        """Calculates and stores final performance metrics after a run."""
        delivered = self.drones_finished
        delivered_count = len(delivered)

        self.metrics["turn_count"] = self.turn_count

        path_costs = [d.path_cost for d in delivered]
        self.metrics["total_path_cost"] = sum(path_costs)

        if self.metrics["turn_count"] > 0:
            self.metrics["drones_moved_per_turn"] = (
                self.metrics["total_path_cost"]
                / (self.metrics["turn_count"] * self.graph.drones_count)
                * 100
            )
        else:
            self.metrics["drones_moved_per_turn"] = 0

        if delivered:
            self.metrics["min_turn"] = min(path_costs)
            self.metrics["max_turn"] = max(path_costs)
            self.metrics["avg_turn_per_drone"] = (
                self.metrics["total_path_cost"] / delivered_count
            )
        else:
            self.metrics["min_turn"] = 0
            self.metrics["max_turn"] = 0
            self.metrics["avg_turn_per_drone"] = 0

    def _assing_path(self, drone: Drone) -> None:
        cheapest_path = None
        for path in self.all_paths:
            if cheapest_path == None \
                or path.get_cost() < cheapest_path.get_cost()
            cheapest_path = path
        drone.path = cheapest_path

    def start_orchestra(self) -> None:
        """
        This method start the simulation, which is going to iterate over each drone
        make a drone move or wait, depending on the better decision
        decision is taken by the pathfinding class, which uses
        Dijsktra's algorithm to find the shortest path but it also
        takes into account occupancy and max_link_capacity constraints,
        or it is only a job for the orchestrator_?
        simulates drones, and send them to the end
        using fictitial drones helps
        
        """

        self.drones_moving = []
        for drone in self.graph.drones:
            next_zone = pathfinder.find_path(drone, graph)
            if next zone is not None 
                drone.move_to(next_zone)
            if next_zone is restricted:
                drone.move_to_but_stay
            else: 
                drone.wait()
            if drone.status == DroneState.LANDED:
                self.drones_moving.append(drone)
            if drone.current_zone == self.graph.end_zone:
                self.drones_finished.append(drone)
                self.drones_finished_count += 1
        while self.drones_finished < self.graph.drones_count:
            drone = Drone()
            links_available = []
            current_zone = drone.current_zone
            best_zone = None
            for link in current_zone.links:
                # Getting all possible zones and selecting the one with less ocupancy
                opposite_zone = link.get_opposite(current_zone.name)
                if opposite_zone.type == ZoneType.RESTRICTED:
                    continue
                occupancy_cost = opposite_zone.get_occupancy()

                if best_zone is None or cost < best_zone.cost:
                    best_zone = opposite_zone

            if not best_zone:
                drone.state = DroneState.WAIT
            self.turn_count += 1
            turn_str = self._turn_to_str()
            self._output_move(turn_str)
