from model import FlyinGraph, Coord
from model.drone import ZoneType
from pathfinding.base import Pathfinding


class AstarPathfinding(Pathfinding):
    def __init__(self):
        super().__init__()

    def find_path(graph: FlyinGraph):
        visited = set[Coord]
        path_sol = list[Coord]
        current = graph.start_zone
        end = graph.end_zone
        visited.add(current)
        while True:
            if current == end:
                break
            adj_zones = graph.get_zone(current).get_adj_zones()
            for c in adj_zones:
                if c.type == ZoneType.BLOCKED:
                    continue
                elif c.type == ZoneType.PRIORITY:
                    winner = c
                elif winner is None:
                    winner = c
                winner = c
            path_sol.append(winner.coord)
            return path_sol


