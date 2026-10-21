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
    def find_all_paths(self) -> list[list[str]]:
        """
        Enumerate every *simple* path (no zone visited twice) from the
        start hub to the end hub, in DFS order.

        Every branch carries its own ``parents`` / ``visited`` copies, so
        branches never share history: that is what turns this from a
        single spanning-tree walk into real path enumeration.

        Args:
            max_paths: optional cap on how many paths are collected, to
                keep the (exponential) enumeration bounded.

        Returns:
            The list of paths (each a list of zone names), ``[]`` when the
            goal cannot be reached.
        """
        all_paths: list[list[str]] = []
        max_paths = min(self.graph.drone_count, 50)
        max_paths_count = 0
        start = self.graph.start_zone.name
        end_zone_name = self.graph.end_zone.name
        first_parents: dict[str, str | None] = {start: None}
        first_visited: set[str] = set()
        first_visited.add(start)
        queue: list[tuple[str, dict[str, str | None], set[str]]] = [
            (start, first_parents, first_visited)
        ]

        while queue:
            zone_name, parents, visited = queue.pop()

            # The goal ends a path: never walk past it, or paths that
            # continue beyond the destination would be emitted too.
            if zone_name == end_zone_name:
                all_paths.append(self._build_path(zone_name, parents))
                max_paths_count += 1
                if max_paths_count >= max_paths:
                    break
                continue

            for neighbour in self.graph.get_neighbors(zone_name):
                if neighbour.is_blocked():
                    continue
                if neighbour.name in visited:
                    continue
                # A dead end with no route to the goal is not worth a
                # branch of its own.
                if self.distance_map.get(neighbour.name, math.inf) == math.inf:
                    continue
                new_parents = dict(parents)
                new_parents[neighbour.name] = zone_name
                new_visited = set(visited)
                new_visited.add(neighbour.name)
                queue.append(
                    (neighbour.name, new_parents, new_visited)
                )
        return all_paths

    def find_shortest_path(self) -> list[str]:
        """
        Cheapest start-to-goal path, as a list of zone names.

        A standard Dijkstra over the same ``static_cost`` model that feeds
        ``distance_map``, so the returned path always agrees with the map
        the orchestrator follows. ``[]`` when the goal is unreachable.
        """
        start_name = self.graph.start_zone.name
        parents: dict[str, str | None] = {start_name: None}
        costs: dict[str, float] = {start_name: 0}
        end_zone_name = self.graph.end_zone.name
        queue: list[tuple[float, str]] = [(0.0, start_name)]

        while queue:
            current_cost, current_name = heapq.heappop(queue)
            if current_cost > costs[current_name]:
                continue
            for neighbour in self.graph.get_neighbors(current_name):
                if neighbour.is_blocked():
                    continue
                # Sum the cost that you have already
                # With the cost to enter the neighbour
                # Depending on zone type
                new_cost = current_cost + neighbour.static_cost
                if new_cost >= costs.get(neighbour.name, math.inf):
                    continue
                costs[neighbour.name] = new_cost
                parents[neighbour.name] = current_name
                heapq.heappush(queue, (new_cost, neighbour.name))
            if current_name == end_zone_name:
                return self._build_path(current_name, parents)
        return []

    @staticmethod
    def _build_path(
        from_zone: str,
        parents: dict[str, str | None],
    ) -> list[str]:
        """
        Walk the ``parents`` map backwards into a start-to-goal path.

        ``parents[start]`` is ``None``, which is what terminates the walk.
        """
        result: list[str] = []
        current: str | None = from_zone
        while current is not None:
            result.append(current)
            current = parents.get(current)
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
