from abc import ABC

from src.model import FlyinGraph, Coord


class Pathfinding(ABC):
    def __init__(self):
        super().__init__()

    def find_path(graph: "FlyinGraph") -> list[Coord]:
        raise NotImplementedError("Not implemented Pathfinding method")