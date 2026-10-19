import heapq
import math

from error.error import FlyinError
from model import FlyinGraph
from model.graph import Zone


class DijkstraPathfinding:
    """
    Distance-first pathfinding.

    ``distance_map`` holds, for every reachable zone, the minimum cost to
    reach the end zone. The orchestrator asks for the *ranked* neighbour
    list (``find_best_zones``) and sends the drone to the cheapest legal
    one each turn.
    """

    def __init__(self, graph: FlyinGraph):
        if graph is None:
            raise FlyinError("Graph is not defined in Pathfinding")
        self.graph = graph
        self._edges = self._build_edges()
        self.distance_map = self._build_distance_map()

    # ---- building ---------------------------------------------------
    def _build_edges(self) -> dict[str, list[tuple[str, int]]]:
        """Adjacency list ``zone -> [(neighbour, cost_to_enter)]``."""
        edges: dict[str, list[tuple[str, int]]] = {}
        for zone in self.graph.all_zones:
            if zone.is_blocked():
                continue
            edges[zone.name] = [
                (neighbour.name, neighbour.static_cost)
                for neighbour in self.graph.get_neighbors(zone.name)
                if not neighbour.is_blocked()
            ]
        return edges

    def _build_distance_map(self) -> dict[str, float]:
        dmap = {
            zone.name: math.inf
            for zone in self.graph.all_zones
            if not zone.is_blocked()
        }
        end = self.graph.end_zone
        if end is None:
            return dmap

        dmap[end.name] = 0
        zones_left: list[tuple[float, str]] = [(0, end.name)]
        while zones_left:
            cost, zone_name = heapq.heappop(zones_left)
            if cost > dmap[zone_name]:
                continue
            for neighbour in self.graph.get_neighbors(zone_name):
                if neighbour.is_blocked():
                    continue
                new_cost = dmap[zone_name] + neighbour.static_cost
                if new_cost < dmap.get(neighbour.name, math.inf):
                    dmap[neighbour.name] = new_cost
                    heapq.heappush(zones_left, (new_cost, neighbour.name))
        return dmap

    # ---- ranking ----------------------------------------------------
    def find_best_zones(self, zone: Zone) -> list[Zone]:
        """
        Rank every reachable neighbour of ``zone``, cheapest first.

        The primary key is the distance-to-goal, so the head of the list
        lies on a shortest path. Occupancy is the tie-breaker, then the
        zone name for a deterministic order. ``inf`` neighbours (dead
        ends) are kept last instead of being banned.
        """
        if zone is None or zone.is_blocked():
            return []

        scored: list[tuple[tuple[float, int, str], Zone]] = []
        for neighbour in self.graph.get_neighbors(zone.name):
            if neighbour.is_blocked():
                continue
            key = (
                self.distance_map.get(neighbour.name, math.inf),
                neighbour.drone_count,
                neighbour.name,
            )
            scored.append((key, neighbour))

        scored.sort(key=lambda item: item[0])
        return [neighbour for _, neighbour in scored]

    def find_best_zone(self, zone: Zone) -> Zone | None:
        """Return the single cheapest neighbour, or ``None`` when stuck."""
        ranked = self.find_best_zones(zone)
        return ranked[0] if ranked else None
