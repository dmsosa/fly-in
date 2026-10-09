from collections import deque

from error.error import FlyinError
from model.drone import Drone
from model import FlyinGraph, Coord


class DijkstraPathfinding:
    def __init__(self, graph: FlyinGraph):
        super().__init__()
        self.graph = graph

    def build_distance_map(self) -> None:
        end = self.graph.end_zone
        dmap = {
            end.name: 0
        }
        zones_left = deque([0, end.name])

        while zones_left:
            cost, zone_name = zones_left.popleft()
            zone = self.graph.get_zone_by_name(zone_name)

            if zone is None:
                raise FlyinError("Zone not found")
            
            for conn in zone.connections:
                opposite_name = conn.get_opposite(zone_name)
                opposite = self.graph.get_zone_by_name(opposite_name)

                if zone is None:
                    raise FlyinError("opposite not found")

                new_cost = cost + zone.get_cost()

                if new_cost < dmap.get(opposite_name, float("inf")):
                    dmap[opposite_name] = new_cost
                    zones_left.append(new_cost, opposite)

        self.distance_map = dmap

    def find_path(drone: Drone, graph: FlyinGraph) -> list[Coord]:
        pass