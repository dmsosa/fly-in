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
        self.distance_map = self._build_distance_map()

    # ---- building ---------------------------------------------------
    def _build_distance_map(self) -> dict[str, float]:
        dmap = {zone.name: math.inf for zone in self.graph.all_zones}
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

    # ---- find all the paths, regardless of if it is the shortest or not ----
    def find_all_paths(self) -> list[str]:
        # To build a way, I dont need the cost, since I dont want to compare them
        all_paths = []
        visited = set()
        parents = {self.graph.start_zone.name: None}
        end_zone_name = self.graph.end_zone.name
        queue = [self.graph.start_zone.name]

        while queue:
            zone_name = heapq.heappop(queue)
            visited.add(zone_name)
            if zone_name == end_zone_name:
                path = self._build_path(zone_name, parents)
                all_paths.append(path)
            for neighbour in self.graph.get_neighbors(zone_name):
                if neighbour.is_blocked():
                    continue
                if neighbour.name in visited:
                    continue
                parents[neighbour.name] = zone_name
                heapq.heappush(queue, neighbour.name)
        return all_paths

    def find_shortest_path(self) -> list[str]:
        # To build a way, I dont need the cost, since I dont want to compare them
        start_name = self.graph.start_zone.name
        visited = set()
        parents = {start_name: None}
        costs = {start_name: 0}
        end_zone_name = self.graph.end_zone.name
        queue = []

        queue.append((0, start_name))
        while queue:
            current_cost, current_name = queue.pop()
            visited.add(current_name)
            if current_name == end_zone_name:
                return self._build_path(current_name, parents)
            for neighbour in self.graph.get_neighbors(current_name):
                if neighbour.is_blocked():
                    continue
                if neighbour.name in visited:
                    continue
                # Sum the cost that you have already
                # With the cost to enter the neighbour
                # Depending on zone type
                new_cost = current_cost + neighbour.static_cost
                if new_cost < costs.get(neighbour.name, math.inf):
                    costs[neighbour.name] = new_cost
                    parents[neighbour.name] = current_name
                    heapq.heappush(queue, neighbour.name)
        return []

    @staticmethod
    def _build_path(
        from_zone: str,
        parents: dict[str, str]
        ) -> list[str]:
        result = [from_zone]
        current = from_zone
        while (current is not None):
            result.append(current)
            current = parents.get(current, None)
        result.reverse()
        return result
    
    
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

    # ---- reachability ------------------------------------------------
    def is_end_reachable(self, start: str | None = None) -> bool:
        """
        ``True`` when ``start`` (the start hub by default) has a path to
        the end zone.

        The distance map is built backwards from the end over an
        *undirected* graph, so a zone without a finite cost-to-go is
        exactly a zone sitting in another connected component.
        """
        origin = start if start is not None else self.graph.start_zone.name
        return self.distance_map.get(origin, math.inf) != math.inf

    def unreachable_zones(self) -> list[str]:
        """
        Sorted names of every non-blocked zone with no route to the goal.

        Used to explain *why* a map is unsolvable (case: the goal itself
        is cut off) and to warn about stray islands on solvable maps.
        """
        return sorted(
            zone.name
            for zone in self.graph.all_zones
            if not zone.is_blocked()
            and self.distance_map.get(zone.name, math.inf) == math.inf
        )
