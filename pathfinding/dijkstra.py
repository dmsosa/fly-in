from src.model import FlyinGraph, Coord
from src.pathfinding.base import Pathfinding


class DijkstraPathfinding(Pathfinding):
    def __init__(self):
        super().__init__()

    def find_path(graph: FlyinGraph) -> list[Coord]:
        pass
        # current = graph.start_zone.coord
        # end = graph.end_zone.coord
        # visited: set[Coord] = {current}
        # possible_queue: 
        # while possible:
        #     if current == end:
        #         return path
        # pass