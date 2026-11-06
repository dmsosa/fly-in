"""Headless tests for the pygame replay (no window is shown).

The tests never open a visible window: SDL runs with the ``dummy`` video
driver. They are written as plain functions so they work under pytest
*and* can be executed directly:

    python3 -m tests.gui.test_pygame_gui
"""
from __future__ import annotations

import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

if __package__ in (None, ""):  # running as a script
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))))

import pygame  # noqa: E402

from gui.pygame_gui import (  # noqa: E402
    HUD_CONTROLS,
    FlyinPygameGui,
    hud_status,
    point_on_segment,
)
from gui.game_loop import Command, Replay  # noqa: E402
from model.graph import FlyinGraph  # noqa: E402
from orchestrator.orchestrator import Move  # noqa: E402
from tests.helpers import make_drone, make_graph  # noqa: E402


# ---------------------------------------------------------------- graphs

def linear_graph() -> FlyinGraph:
    """``start -- a -- b -- goal``, room for two drones at the goal."""
    return make_graph(
        drone_count=2,
        start=("start", (0, 0)),
        end=("goal", (3, 0)),
        zones=[
            {"name": "a", "coord": (1, 0)},
            {"name": "b", "coord": (2, 0)},
        ],
        connections=[("start", "a"), ("a", "b"), ("b", "goal")],
        end_max_drones=2,
    )


def restricted_graph() -> FlyinGraph:
    """``start -- r(restricted) -- goal``."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[{"name": "r", "coord": (1, 0), "type": "restricted"}],
        connections=[("start", "r"), ("r", "goal")],
    )


def diagonal_graph() -> FlyinGraph:
    """``start -- r(restricted) -- goal`` along a diagonal link."""
    return make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (4, 0)),
        zones=[{"name": "r", "coord": (2, 2), "type": "restricted"}],
        connections=[("start", "r"), ("r", "goal")],
    )


HISTORY = [
    [Move(0, "D1", "a")],
    [Move(1, "D1", "b"), Move(1, "D2", "a")],
    [Move(2, "D1", "goal"), Move(2, "D2", "b")],
    [Move(3, "D2", "goal")],
]

# Expected (from_zone, to_zone) per drone per turn, derived by hand.
EXPECTED = {
    "D1": [
        ("start", "a"),
        ("a", "b"),
        ("b", "goal"),
        ("goal", "goal"),     # delivered: no move in turn 3
    ],
    "D2": [
        ("start", "start"),   # did not move in turn 0
        ("start", "a"),
        ("a", "b"),
        ("b", "goal"),
    ],
}


# ---------------------------------------------------------------- helpers

def make_gui(
    graph: FlyinGraph | None = None,
    history: list[list[Move]] | None = None,
    drone_ids: tuple[str, ...] = ("D1", "D2"),
) -> FlyinPygameGui:
    graph = graph if graph is not None else linear_graph()
    history = history if history is not None else HISTORY
    drones = {
        drone_id: make_drone(graph, graph.start_zone.name, drone_id)
        for drone_id in drone_ids
    }
    return FlyinPygameGui(graph=graph, drones=drones, history=history)


def zone_px(gui: FlyinPygameGui, zone_name: str) -> tuple[float, float]:
    zone = gui.graph.get_zone_by_name(zone_name)
    assert zone is not None, f"unknown zone {zone_name!r} in test graph"
    return gui.to_pixel(*zone.coord)


def assert_close(
    got: tuple[float, float],
    want: tuple[float, float],
    tol: float = 1e-6,
    label: str = "",
) -> None:
    assert abs(got[0] - want[0]) <= tol and abs(got[1] - want[1]) <= tol, (
        f"{label}: got {got}, want {want}"
    )


def assert_in_zone(
    gui: FlyinPygameGui,
    point: tuple[float, float],
    zone_name: str,
) -> None:
    center = zone_px(gui, zone_name)
    distance = math.dist(point, center)
    assert distance <= gui.zone_radius + 1, (
        f"{point} is {distance:.1f}px from {zone_name!r}, "
        f"outside its {gui.zone_radius}px radius"
    )


def assert_between(
    point: tuple[float, float],
    origin: tuple[float, float],
    dest: tuple[float, float],
    tol: float = 1e-6,
) -> None:
    low_x, high_x = sorted((origin[0], dest[0]))
    low_y, high_y = sorted((origin[1], dest[1]))
    assert low_x - tol <= point[0] <= high_x + tol
    assert low_y - tol <= point[1] <= high_y + tol, (
        f"{point} is outside the box {low_x, high_x} x {low_y, high_y}"
    )


# ------------------------------------------------------------ timelines

def test_timeline_has_one_segment_per_turn() -> None:
    """A dense timeline = one segment per drone per turn, always."""
    gui = make_gui()
    for drone_id, timeline in gui.timelines.items():
        assert len(timeline) == len(HISTORY), (
            f"{drone_id}: {len(timeline)} segments for "
            f"{len(HISTORY)} turns"
        )


def test_timeline_segments_chain_without_gaps() -> None:
    """The end of turn t is the start of turn t+1."""
    gui = make_gui()
    for drone_id, timeline in gui.timelines.items():
        for turn in range(1, len(timeline)):
            assert_close(
                timeline[turn].from_px,
                timeline[turn - 1].to_px,
                label=f"{drone_id} gap at turn {turn}",
            )


def test_timeline_tracks_each_drone_independently() -> None:
    """A drone that does not move gets X -> X, not another drone's move."""
    gui = make_gui()
    d1 = gui.timelines["D1"]
    d2 = gui.timelines["D2"]

    assert_in_zone(gui, d1[0].from_px, "start")
    assert_in_zone(gui, d1[0].to_px, "a")

    assert_in_zone(gui, d2[0].from_px, "start")
    assert_in_zone(gui, d2[0].to_px, "start")
    assert d1[0].to_px != d2[0].to_px


def test_timeline_matches_expected_route() -> None:
    """Every (from, to) pair stays inside the expected zone."""
    gui = make_gui()
    for drone_id, expected in EXPECTED.items():
        timeline = gui.timelines[drone_id]
        for turn, (origin_name, dest_name) in enumerate(expected):
            assert_in_zone(gui, timeline[turn].from_px, origin_name)
            assert_in_zone(gui, timeline[turn].to_px, dest_name)


def test_timeline_ends_in_goal() -> None:
    gui = make_gui()
    for drone_id, timeline in gui.timelines.items():
        assert_in_zone(gui, timeline[-1].to_px, "goal")


def test_restricted_crossing_stops_on_the_link() -> None:
    """``"start-r"`` ends on the link, the next turn lands in ``r``."""
    history = [
        [Move(0, "D1", "start-r")],   # departure: ride the link
        [Move(1, "D1", "r")],         # landing
        [Move(2, "D1", "goal")],
    ]
    gui = make_gui(
        graph=restricted_graph(), history=history, drone_ids=("D1",))
    timeline = gui.timelines["D1"]
    start = zone_px(gui, "start")
    restricted = zone_px(gui, "r")

    transit = timeline[0].to_px
    assert_between(transit, start, restricted)
    assert math.dist(transit, start) >= gui.zone_radius
    assert math.dist(transit, restricted) >= gui.zone_radius

    assert_close(timeline[1].from_px, transit, label="landing start")
    assert_in_zone(gui, timeline[1].to_px, "r")
    assert_in_zone(gui, timeline[2].to_px, "goal")


def test_transit_holds_the_link_for_extra_turns() -> None:
    """If the restricted zone is full, the drone rests on the link."""
    history = [
        [Move(0, "D1", "start-r")],
        [],                            # no move: still holding the link
        [Move(2, "D1", "r")],
    ]
    gui = make_gui(
        graph=restricted_graph(), history=history, drone_ids=("D1",))
    timeline = gui.timelines["D1"]

    assert_close(timeline[1].from_px, timeline[0].to_px)
    assert_close(timeline[1].to_px, timeline[0].to_px)
    assert_close(timeline[2].from_px, timeline[0].to_px)


def test_two_drones_on_the_same_link() -> None:
    """Two transit drones are spread along the link, not stacked."""
    history = [[
        Move(0, "D1", "start-r"),
        Move(0, "D2", "start-r"),
    ]]
    gui = make_gui(graph=restricted_graph(), history=history)
    start = zone_px(gui, "start")
    restricted = zone_px(gui, "r")

    first = gui.timelines["D1"][0].to_px
    second = gui.timelines["D2"][0].to_px

    assert first[0] < second[0]
    assert_between(first, start, restricted)
    assert_between(second, start, restricted)
    assert math.dist(first, second) > 1.0


def test_build_timeline_is_idempotent() -> None:
    gui = make_gui()
    first = {d: list(t) for d, t in gui.timelines.items()}
    gui._build_timeline()
    for drone_id, timeline in gui.timelines.items():
        assert timeline == first[drone_id], (
            f"{drone_id}: rebuilding changed the timeline"
        )


def test_empty_history_renders_start_position() -> None:
    """No turns: every drone is in the start hub, no IndexError."""
    gui = make_gui(history=[])
    for drone_id in gui.drones:
        point = gui._get_drone_pixels(0.0, drone_id)
        assert_in_zone(gui, point, "start")


def test_timeline_turn_ids_match_their_index() -> None:
    """``segment.turn_id`` is the turn the segment belongs to."""
    gui = make_gui()
    for drone_id, timeline in gui.timelines.items():
        for index, segment in enumerate(timeline):
            assert segment.turn_id == index, (
                f"{drone_id} segment {index} says turn {segment.turn_id}"
            )


# ------------------------------------------------------------- offsets

def test_lone_drone_is_centered_in_a_zone() -> None:
    gui = make_gui()
    center = zone_px(gui, "start")
    assert_close(gui._offset_pixels("start", 0, 1), center)


def test_zone_slots_are_distinct_and_inside_the_hub() -> None:
    gui = make_gui()
    center = zone_px(gui, "start")
    points = [gui._offset_pixels("start", slot, 4) for slot in range(4)]

    assert len(set(points)) == 4, f"slots overlap: {points}"
    for point in points:
        assert math.dist(point, center) <= gui.zone_radius + 1


def test_link_midpoint_for_a_lone_drone() -> None:
    gui = make_gui(graph=restricted_graph(), history=[], drone_ids=("D1",))
    start = zone_px(gui, "start")
    restricted = zone_px(gui, "r")
    midpoint = ((start[0] + restricted[0]) / 2,
                (start[1] + restricted[1]) / 2)

    assert_close(gui._offset_pixels("start-r", 0, 1), midpoint)


def test_link_slots_are_ordered() -> None:
    gui = make_gui(graph=restricted_graph(), history=[], drone_ids=("D1",))
    points = [gui._offset_pixels("start-r", slot, 3) for slot in range(3)]
    assert points[0][0] < points[1][0] < points[2][0]


def test_link_point_stays_between_the_endpoints() -> None:
    """Diagonal links keep the drone inside the endpoints' box."""
    gui = make_gui(graph=diagonal_graph(), history=[], drone_ids=("D1",))
    start = zone_px(gui, "start")
    restricted = zone_px(gui, "r")

    for slot in range(3):
        point = gui._offset_pixels("start-r", slot, 3)
        assert_between(point, start, restricted)


def test_point_on_segment_keeps_the_margin() -> None:
    first = point_on_segment((0, 0), (100, 0), 0, 2, margin=0.2)
    second = point_on_segment((0, 0), (100, 0), 1, 2, margin=0.2)
    assert_close(first, (40.0, 0.0))
    assert_close(second, (60.0, 0.0))


def test_drone_radius_shrinks_when_crowded() -> None:
    gui = make_gui()
    assert gui._drone_radius(1) == gui.drone_radius

    radii = [gui._drone_radius(n) for n in (2, 4, 10, 25)]
    assert all(a >= b for a, b in zip(radii, radii[1:])), radii
    assert radii[-1] < gui.drone_radius
    assert radii[-1] >= 2.0


def test_segment_carries_slot_counts() -> None:
    """The renderer needs the crowding of both endpoints."""
    gui = make_gui()
    first = gui.timelines["D1"][0]
    assert (first.from_count, first.to_count) == (2, 1)


def test_point_on_segment_clamps_slot_and_margin() -> None:
    origin, dest = (0.0, 0.0), (100.0, 0.0)
    assert_close(
        point_on_segment(origin, dest, -5, 3),
        point_on_segment(origin, dest, 0, 3),
    )
    assert_close(
        point_on_segment(origin, dest, 99, 3),
        point_on_segment(origin, dest, 2, 3),
    )
    # An absurd margin is clamped, but the point never leaves the segment.
    point = point_on_segment(origin, dest, 1, 2, margin=10.0)
    assert 0.0 <= point[0] <= 100.0


# -------------------------------------------------------- interpolation

def test_lone_drone_endpoints_and_midpoint() -> None:
    gui = make_gui(
        history=[[Move(0, "D1", "a")]], drone_ids=("D1",))
    start = zone_px(gui, "start")
    a = zone_px(gui, "a")
    midpoint = ((start[0] + a[0]) / 2, (start[1] + a[1]) / 2)

    assert_close(gui._get_drone_pixels(0.0, "D1"), start, label="t=0")
    assert_close(gui._get_drone_pixels(0.5, "D1"), midpoint, label="t=0.5")
    assert_close(gui._get_drone_pixels(1.0, "D1"), a, label="t=1")


def test_shared_zone_splits_drones() -> None:
    """Two drones waiting in ``start`` get two different slots."""
    gui = make_gui(history=[[], []])
    first = gui._get_drone_pixels(0.0, "D1")
    second = gui._get_drone_pixels(0.0, "D2")

    assert math.dist(first, second) > 1.0
    assert_in_zone(gui, first, "start")
    assert_in_zone(gui, second, "start")


def test_drone_pixels_at_turn_boundary_are_continuous() -> None:
    gui = make_gui()
    for turn in range(len(HISTORY)):
        assert_close(
            gui._get_drone_pixels(float(turn + 1), "D1"),
            gui.timelines["D1"][turn].to_px,
            label=f"end of turn {turn}",
        )


def test_drone_pixels_clamped_at_the_end() -> None:
    gui = make_gui()
    end = float(len(HISTORY))
    assert_in_zone(gui, gui._get_drone_pixels(end, "D2"), "goal")
    assert_in_zone(gui, gui._get_drone_pixels(end + 10.0, "D2"), "goal")


# -------------------------------------------------------------- replay

def test_replay_pause_stops_the_clock() -> None:
    replay = Replay(end=5.0, turns_per_second=2.0)
    replay.handle([Command.PAUSE])
    replay.advance(0.5)
    assert replay.now == 0.0
    replay.handle([Command.PAUSE])
    replay.advance(0.5)          # 0.5 s * 2 turns/s = 1 turn
    assert replay.now == 1.0


def test_replay_step_forward_and_back() -> None:
    replay = Replay(end=5.0)
    replay.now = 2.4

    replay.handle([Command.NEXT])
    assert replay.now == 3.0, "NEXT completes the current turn"
    assert replay.paused, "stepping must hold the frame"

    replay.handle([Command.PREVIOUS])
    assert replay.now == 2.0, "PREVIOUS rewinds to the turn start"
    assert replay.paused


def test_replay_previous_from_turn_start() -> None:
    replay = Replay(end=5.0)
    replay.now = 3.0
    replay.handle([Command.PREVIOUS])
    assert replay.now == 2.0


def test_replay_step_is_clamped() -> None:
    replay = Replay(end=3.0)
    replay.handle([Command.PREVIOUS])
    assert replay.now == 0.0
    replay.now = 3.0
    replay.handle([Command.NEXT])
    assert replay.now == 3.0


def test_replay_reset_and_quit() -> None:
    replay = Replay(end=5.0)
    replay.now = 4.0
    replay.handle([Command.RESET])
    assert replay.now == 0.0 and replay.paused
    replay.handle([Command.QUIT])
    assert not replay.running


def test_replay_advance_is_clamped_to_end() -> None:
    replay = Replay(end=1.0, turns_per_second=4.0)
    replay.advance(10.0)
    assert replay.now == 1.0


# --------------------------------------------------------------- HUD

def test_hud_status_labels() -> None:
    assert hud_status(0.0, 10, False) == ("Turn 1/10", "PLAYING")
    assert hud_status(3.2, 10, True) == ("Turn 4/10", "PAUSED")
    assert hud_status(10.0, 10, False) == ("Turn 10/10", "PLAYING")
    assert hud_status(0.0, 0, False) == ("Turn 0/0", "PLAYING")


def test_hud_controls_list_pause_next_previous() -> None:
    actions = {action for _, action in HUD_CONTROLS}
    assert {"Pause", "Next", "Previous"} <= actions


def test_hud_draws_bottom_bar_and_leaves_the_graph() -> None:
    """Only the bottom strip belongs to the HUD."""
    gui = make_gui()
    gui.font = gui._load_font()
    background = pygame.Color(gui.color_theme["bg"])
    bar = pygame.Color(gui.color_theme["bg-secondary"])

    gui.screen.fill(background)
    gui._draw_hud(0.0, float(len(HISTORY)), False)

    top = gui.screen.get_at((10, 10))[:3]
    bottom = gui.screen.get_at((10, gui.window_h - 10))[:3]
    assert top == (background.r, background.g, background.b), (
        f"top-left pixel is {top}: the HUD painted over the graph"
    )
    assert bottom == (bar.r, bar.g, bar.b), (
        f"bottom pixel is {bottom}: the HUD bar is missing"
    )


def test_render_draws_one_frame() -> None:
    """A single frame must render; ``_render`` reads no stale fields."""
    gui = make_gui()
    gui.font = gui._load_font()
    gui._render(Replay(end=float(len(HISTORY))))


def test_draw_graph_handles_unlimited_capacity_hubs() -> None:
    """Start/end hubs have ``max_drones=None`` on real maps."""
    graph = make_graph(
        drone_count=1,
        start=("start", (0, 0)),
        end=("goal", (2, 0)),
        zones=[{"name": "a", "coord": (1, 0)}],
        connections=[("start", "a"), ("a", "goal")],
        start_max_drones=None,   # type: ignore[arg-type]
        end_max_drones=None,     # type: ignore[arg-type]
    )
    gui = make_gui(
        graph=graph,
        history=[[Move(0, "D1", "goal")]],
        drone_ids=("D1",),
    )
    gui.font = gui._load_font()
    gui.draw_graph()


# ---------------------------------------------------------- frame loop

class _FakeEvent:
    def __init__(self, type_: int, key: int | None = None) -> None:
        self.type = type_
        self.key = key


class _FakeClock:
    """Alternates one frame of time and an immediate second read (0 ms)."""

    def __init__(self) -> None:
        self.calls = 0

    def tick(self, fps: int = 0) -> int:
        value = 16 if self.calls % 2 == 0 else 0
        self.calls += 1
        return value


class _Driver:
    """Feeds a scripted event queue and records what gets drawn."""

    def __init__(self, script: list[list[_FakeEvent]]) -> None:
        self.script = script
        self.frame = 0
        self.advances: list[float] = []

    def events(self) -> list[_FakeEvent]:
        index = self.frame
        self.frame += 1
        if index < len(self.script):
            return self.script[index]
        return [_FakeEvent(pygame.QUIT)]


def run_loop(
    gui: FlyinPygameGui,
    script: list[list[_FakeEvent]],
) -> tuple[_Driver, list[tuple[int, float, float]]]:
    driver = _Driver(script)
    real_clock = pygame.time.Clock
    real_get = pygame.event.get
    real_advance = Replay.advance
    real_draw = FlyinPygameGui._draw_drone
    draws: list[tuple[int, float, float]] = []

    def fake_advance(self: Replay, dt: float) -> None:
        driver.advances.append(dt)
        real_advance(self, dt)

    def fake_draw(
        self: FlyinPygameGui,
        px: float,
        py: float,
        radius: float | None = None,
    ) -> None:
        draws.append((driver.frame, px, py))

    pygame.time.Clock = _FakeClock  # type: ignore[assignment]
    pygame.event.get = driver.events  # type: ignore[assignment]
    Replay.advance = fake_advance  # type: ignore[assignment]
    FlyinPygameGui._draw_drone = fake_draw  # type: ignore[assignment]
    try:
        gui.draw_history()
    finally:
        pygame.time.Clock = real_clock  # type: ignore[assignment]
        pygame.event.get = real_get  # type: ignore[assignment]
        Replay.advance = real_advance  # type: ignore[assignment]
        FlyinPygameGui._draw_drone = real_draw  # type: ignore[assignment]

    return driver, draws


def test_loop_advances_time_from_a_single_clock_read() -> None:
    """Two ``clock.tick`` calls per frame leave the used dt at ~0."""
    gui = make_gui()
    driver, _ = run_loop(gui, [[] for _ in range(4)])
    assert driver.advances, "advance() was never called"
    assert max(driver.advances) > 0.01, (
        "the replay clock never advanced; is clock.tick called twice "
        f"per frame? dts={driver.advances}"
    )


def test_paused_replay_keeps_rendering_and_stepping() -> None:
    """PAUSE must freeze time, not the screen; NEXT must redraw."""
    gui = make_gui()
    script = [
        [],
        [_FakeEvent(pygame.KEYDOWN, pygame.K_p)],      # pause
        [_FakeEvent(pygame.KEYDOWN, pygame.K_RIGHT)],  # step forward
        [_FakeEvent(pygame.QUIT)],
    ]
    driver, draws = run_loop(gui, script)

    paused_frames = [d for d in draws if d[0] >= 2]
    assert paused_frames, (
        "nothing was drawn while paused; rendering is gated by paused"
    )

    stepped_frames = [d for d in draws if d[0] == 3]
    before_step = [d for d in draws if d[0] == 2]
    assert stepped_frames and before_step, f"missing frames; draws={draws}"
    assert stepped_frames[0][1:] != before_step[0][1:], (
        "NEXT did not move the drones on screen"
    )


# --------------------------------------------------------------- runner

def main() -> int:
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    failures = 0
    for name, test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001 - test runner
            failures += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {name}")
    print(f"\n{len(tests) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
