"""Fixtures shared across the test-suite."""
from __future__ import annotations

import pytest

from model.graph import FlyinGraph
from tests.helpers import make_graph


@pytest.fixture
def linear_graph() -> FlyinGraph:
    """``start -- a -- b -- goal`` (a plain linear path)."""
    return make_graph(
        drone_count=2,
        start=("start", (0, 0)),
        end=("goal", (3, 0)),
        zones=[
            {"name": "a", "coord": (1, 0)},
            {"name": "b", "coord": (2, 0)},
        ],
        connections=[("start", "a"), ("a", "b"), ("b", "goal")],
    )


@pytest.fixture
def fork_graph() -> FlyinGraph:
    """A short branch (``a``) and a longer one (``c-d-e``)."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (5, 0)),
        zones=[
            {"name": "a", "coord": (1, 0)},
            {"name": "c", "coord": (1, 1)},
            {"name": "d", "coord": (2, 1)},
            {"name": "e", "coord": (3, 1)},
        ],
        connections=[
            ("start", "a"), ("a", "goal"),
            ("start", "c"), ("c", "d"), ("d", "e"), ("e", "goal"),
        ],
    )


@pytest.fixture
def restricted_graph() -> FlyinGraph:
    """``start -- r(restricted) -- goal``."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[{"name": "r", "coord": (1, 0), "type": "restricted"}],
        connections=[("start", "r"), ("r", "goal")],
    )


@pytest.fixture
def blocked_graph() -> FlyinGraph:
    """``start -- wall(blocked)`` and ``start -- a -- goal``."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[
            {"name": "a", "coord": (1, 1)},
            {"name": "wall", "coord": (1, 0), "type": "blocked"},
        ],
        connections=[("start", "wall"), ("start", "a"), ("a", "goal")],
    )


@pytest.fixture
def blocked_dead_end_graph() -> FlyinGraph:
    """The start zone's only neighbour is blocked."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (5, 5)),
        zones=[{"name": "wall", "coord": (1, 0), "type": "blocked"}],
        connections=[("start", "wall")],
    )


@pytest.fixture
def island_graph() -> FlyinGraph:
    """An isolated zone that no drone can reach."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (3, 0)),
        zones=[{"name": "island", "coord": (5, 5)}],
        connections=[("start", "goal")],
    )
