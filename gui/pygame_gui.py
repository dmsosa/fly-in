from dataclasses import dataclass
import math
import os
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from gui.constants import THEME_COLOR
from gui.game_loop import Command, GameLoop, key_commands, poll_events
from model import FlyinGraph
from model.drone import Drone
from orchestrator.orchestrator import Move


os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


FPS = 60
HUD_HEIGHT = 80
ZONE_RADIUS = 15
ZONE_RING_RADIUS = 7
DRONE_RADIUS = 4
ANIM_DURATION = 1.0

#: Bottom-bar menu: (keycap, label, command), in display order.
HUD_CONTROLS: tuple[tuple[str, str, Command], ...] = (
    ("RIGHT", "Next step", Command.NEXT),
    ("LEFT", "Previous step", Command.PREVIOUS),
    ("SPACE", "Play/Pause", Command.PAUSE),
    ("F", "Skip", Command.SKIP),
    ("ESC", "Exit", Command.QUIT),
)


@dataclass(frozen=True)
class Segment:
    turn_id: float
    from_px: tuple[float, float]
    to_px: tuple[float, float]


class FlyinPygameGui(BaseModel):
    """
    Graphical User Interface for Fly-in
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    graph: FlyinGraph
    drones: dict[str, Drone]
    history: list[list[Move]]
    padding: int = Field(default=50)
    min_x: int = Field(default=1)
    max_x: int = Field(default=1)
    min_y: int = Field(default=1)
    max_y: int = Field(default=1)
    color_theme: dict[str, Any] = THEME_COLOR
    turns_per_second: float = Field(default=1.0, gt=0)
    drone_radius: int = Field(default=DRONE_RADIUS, ge=1)
    anim_duration: float = Field(default=ANIM_DURATION, gt=0)
    fps: int = Field(default=FPS, ge=1)
    zone_radius: int = Field(default=ZONE_RADIUS, ge=1)
    zone_ring_radius: int = Field(default=ZONE_RING_RADIUS, ge=1)
    hud_height: int = Field(default=HUD_HEIGHT, ge=1)

    # Runtime state. Pydantic v2 crashes if we set attributes
    # that are not declared as fields. So every value created in
    # model_post_init (or later) needs a field here.
    screen: Any = Field(default=None, exclude=True)
    font: Any = Field(default=None, exclude=True)
    hud_font: Any = Field(default=None, exclude=True)
    hud_buttons: list[tuple[Any, Command]] = Field(
        default_factory=list, exclude=True)
    scale: float = Field(default=0.0, exclude=True)
    offset_x: float = Field(default=0.0, exclude=True)
    offset_y: float = Field(default=0.0, exclude=True)
    window_w: int = Field(default=0, exclude=True)
    window_h: int = Field(default=0, exclude=True)
    timelines: dict[str, list[Segment]] = Field(
        default_factory=dict, exclude=True
        )

    def model_post_init(self, _context: Any) -> None:
        if not PYGAME_AVAILABLE:
            raise ImportError(
                "Error: Pygame is not installed. "
                "GUI can not run"
                )

        pygame.init()

        # Desktop resolution, independent of the window opened before.
        # ``pygame.display.Info()`` reports the *current* mode, so using it
        # here would shrink the window on every new GUI instance and can
        # even make ``scale`` negative (an inverted map).
        get_desktop_sizes = getattr(
            pygame.display, "get_desktop_sizes", None)
        if get_desktop_sizes is not None:
            desktop_w, desktop_h = get_desktop_sizes()[0]
        else:
            info = pygame.display.Info()
            desktop_w, desktop_h = info.current_w, info.current_h

        # 75% of the desktop, never below a usable minimum
        self.window_w = max(320, int(desktop_w * 0.75))
        self.window_h = max(240, int(desktop_h * 0.75))

        self.screen = pygame.display.set_mode((self.window_w, self.window_h))
        pygame.display.set_caption("DS Fly-In ! :v")

        # Calculating mapping from X, Y coordinates to pixels
        # Inside pygame window
        all_zone_x_coords = [z.coord[0] for z in self.graph.all_zones]
        all_zone_y_coords = [z.coord[1] for z in self.graph.all_zones]

        self.min_x = min(all_zone_x_coords)
        self.max_x = max(all_zone_x_coords)
        self.min_y = min(all_zone_y_coords)
        self.max_y = max(all_zone_y_coords)

        range_x = max(self.max_x - self.min_x, 1)
        range_y = max(self.max_y - self.min_y, 1)

        inset_x = self.padding + self.zone_radius
        inset_y = self.padding + self.zone_radius

        usable_w = max(1, self.window_w - 2 * inset_x)
        usable_h = max(1, (self.window_h - 2 * inset_y) - self.hud_height)

        scale_x = usable_w // range_x
        scale_y = usable_h // range_y

        # Never let the mapping collapse or invert on a small window.
        self.scale = max(1, min(scale_x, scale_y))

        # X coordinate needs to start from the left, but not
        # from the left of the entire window size, but
        # from the left of the area used for drawing the graph
        # and also taking into account the padding with 2 * padding
        self.offset_x = inset_x + (
            usable_w - range_x * self.scale) // 2
        self.offset_y = inset_y + (
            usable_h - range_y * self.scale) // 2

    def to_pixel(self, x: int, y: int) -> tuple[int, int]:
        px = self.offset_x + (x - self.min_x) * self.scale
        py = self.offset_y + (y - self.min_y) * self.scale
        return int(px), int(py)

    def _draw_zone(self, zone) -> None:
        """Draws the given zone on the screen"""
        px, py = self.to_pixel(zone.coord[0], zone.coord[1])
        if zone.color:
            try:
                hex_code = self.color_theme.get(
                    zone.color,
                    self.color_theme["secondary"]
                    )
                color = pygame.Color(hex_code)
            except ValueError:
                color = pygame.Color(self.color_theme["secondary"])
        else:
            color = pygame.Color(self.color_theme["secondary"])
        capacity = zone.max_drones if zone.max_drones else math.inf
        is_high_capacity = capacity > 3
        if is_high_capacity:
            radius = self.zone_radius + 5
        else:
            radius = self.zone_radius
        pygame.draw.circle(
            self.screen,
            pygame.Color(self.color_theme["tertiary"]),
            (px, py),
            radius=radius
            )
        pygame.draw.circle(
            self.screen,
            pygame.Color(color),
            (px, py),
            radius=(radius - 2)
        )

    def _draw_connection(
            self,
            origin: tuple[int, int],
            dest: tuple[int, int],
            color: pygame.Color,
            thickness: int,
            dashed: bool = False
            ) -> None:
        # a connection is to  draw a line from origin to dest
        if not dashed:
            pygame.draw.line(
                self.screen,
                pygame.Color(color),
                origin,
                dest,
                thickness
                )
            return

        diff_x = dest[0] - origin[0]
        diff_y = dest[1] - origin[1]
        length = max(1, (diff_x**2 + diff_y**2)**0.5)

        visual_x, visual_y = diff_x / length, diff_y / length

        dash_len, gap_len = 16, 4
        i = 0
        drawing = True

        while i < length:
            segment_len = min(dash_len if drawing else gap_len, length - i)
            if drawing:
                start = (
                    origin[0] + visual_x * i,
                    origin[1] + visual_y * i
                    )
                end = (
                    origin[0] + visual_x * (i + segment_len),
                    origin[1] + visual_y * (i + segment_len)
                    )
                pygame.draw.line(self.screen, color, start, end, thickness)
            i += segment_len
            drawing = not drawing

    def _offset_pixels(
            self,
            place_name: str,
            slot_occupancy: tuple[int, int]
    ) -> tuple[float, float]:
        index, max_slot = slot_occupancy
        if "-" in place_name:
            origin, dest = place_name.split("-")
            xa, ya = self._get_pixels_of_zone(origin)
            xb, yb = self._get_pixels_of_zone(dest)
            f = (index + 1) / (max_slot + 1)  # 1/2, 1/3 & 2/3 for two
            cx = xa + (xb - xa) * f
            cy = ya + (yb - ya) * f
            return cx, cy

        cx, cy = self._get_pixels_of_zone(place_name)
        if max_slot <= 1:
            return cx, cy
        angle = 2 * math.pi * index / max_slot - math.pi / 2
        offset_x = self.zone_ring_radius * math.cos(angle)
        offset_y = self.zone_ring_radius * math.sin(angle)
        return cx + offset_x, cy + offset_y

    def _find_slots(
            self,
            drone_to_zone: dict[str, str]
            ) -> dict[str, tuple[int, int]]:
        """
        (slot, count) of every drone, grouped by the
        place it rests in.
        """
        place_members: dict[str, list[str]] = {}
        for drone_id, place_name in drone_to_zone.items():
            place_members.setdefault(place_name, []).append(drone_id)

        slots: dict[str, tuple[int, int]] = {}
        for drones_in_place in place_members.values():
            for idx, drone_id in enumerate(sorted(drones_in_place)):
                slots[drone_id] = (idx, len(drones_in_place))
        return slots

    def _get_pixels_of_zone(self, zone_name: str) -> tuple[float, float]:
        zone = self.graph.get_zone_by_name(zone_name)
        if not zone:
            return (0, 0)
        x, y = zone.coord
        px, py = self.to_pixel(x, y)
        return (px, py)

    def _build_timelines(self) -> None:
        start = self.graph.start_zone.name
        timelines: dict[str, list[Segment]] = {
            drone_id: [] for drone_id in self.drones.keys()
        }

        drone_to_place: dict[str, str] = {
            drone_id: start
            for drone_id in self.drones.keys()
            }

        # each turn appends a new segment for each drone
        for turn_id, turn in enumerate(self.history):
            origin_place = dict(drone_to_place)  # snapshot

            for move in turn:
                # if this drone moved, append its dest to the goal
                drone_that_moved = move.drone_id
                drone_to_place[drone_that_moved] = move.target_name

            origin_slots = self._find_slots(origin_place)
            end_slots = self._find_slots(drone_to_place)

            for drone_id, timeline in timelines.items():
                # Drone can end on the middle of a connection
                # after having tried to access a restricted zone
                origin_name = origin_place[drone_id]
                end_name = drone_to_place[drone_id]

                from_px = self._offset_pixels(
                    origin_name,
                    origin_slots[drone_id]
                    )
                to_px = self._offset_pixels(
                    end_name,
                    end_slots[drone_id]
                    )
                segment = Segment(
                        turn_id=float(turn_id),
                        from_px=from_px,
                        to_px=to_px
                        )
                timeline.append(segment)

        self.timelines = timelines

    def draw_history(self) -> None:
        """
        simple loop
        The standard Pygame loop order is:

        Handle events (pygame.event.get())
        Update game logic (using dt)
        Draw / render
        clock.tick(60)
        this loop runs about 60 times a second,
        since clock.tick help us to wait the necessary
        amount of time to achieve around 60 iterations
        in 1 second.
        """
        self.font = self._load_font()
        self.hud_font = self._load_font(14)
        clock = pygame.time.Clock()
        pygame.font.init()
        keymap = key_commands()
        self._build_timelines()
        loop = GameLoop(
            end=float(len(self.history)),
            turns_per_second=self.turns_per_second
            )

        while loop.running:
            dt = clock.tick(self.fps) / 1000.0  # Seconds passed
            # current time determines actually in which turn we are placed on
            # Handling pygame events like key pressings and HUD clicks
            loop.handle(poll_events(keymap, self._command_at))
            if not loop.running:
                break
            loop.advance(dt)

            # Draw every frame: pausing freezes the clock, not the screen,
            # so the menu and the ``PAUSED`` badge stay visible and a
            # step/click redraws immediately.
            self._render(loop)

            pygame.display.flip()

        pygame.quit()

    def _render_graph(self) -> None:
        """Draws the connections and zones on the screen"""
        for conn in self.graph.connections:
            name_a, name_b = conn.get_zone_names()
            zone_a = self.graph.get_zone_by_name(name_a)
            zone_b = self.graph.get_zone_by_name(name_b)
            if zone_a is None or zone_b is None:
                continue
            x1, y1 = zone_a.coord
            x2, y2 = zone_b.coord
            coord_pixels1 = self.to_pixel(x1, y1)
            coord_pixels2 = self.to_pixel(x2, y2)

            is_high_capacity = conn.max_link_capacity > 1
            if is_high_capacity:
                color = self.color_theme["connection-primary"]
            else:
                color = self.color_theme["connection-secondary"]
            self._draw_connection(
                coord_pixels1, coord_pixels2,
                color=pygame.Color(color),
                thickness=min(5, max(1, conn.max_link_capacity)),
                dashed=not is_high_capacity
            )

        for zone in self.graph.all_zones:
            self._draw_zone(zone)

    def _render(self, loop: GameLoop) -> None:
        self.screen.fill(pygame.Color(self.color_theme["bg"]))
        self._render_graph()
        for drone_id in self.timelines.keys():
            px, py = self._get_drone_pixels(loop.now, drone_id)
            self._draw_drone(px, py)

        self._draw_hud(loop.now, loop.end, loop.paused)

    def _get_drone_pixels(
            self,
            current_time: float,
            drone_id: str
            ) -> tuple[float, float]:
        timeline = self.timelines.get(drone_id, [])
        if not timeline:                   # no turn recorded yet
            return self._get_pixels_of_zone(self.graph.start_zone.name)

        turn = max(0, min(int(current_time), len(timeline) - 1))

        seg = timeline[turn]

        p = max(
            0.0,
            min(
                1.0,
                (current_time - seg.turn_id) / self.anim_duration
                )
            )
        px = seg.from_px[0] + (seg.to_px[0] - seg.from_px[0]) * p
        py = seg.from_px[1] + (seg.to_px[1] - seg.from_px[1]) * p

        return px, py

    def _draw_drone(
            self,
            px: float,
            py: float
            ) -> None:
        pos = (round(px), round(py))
        pygame.draw.circle(
            self.screen,
            pygame.Color(self.color_theme["drone"]),
            pos,
            self.drone_radius
        )
        pygame.draw.circle(
            self.screen,
            pygame.Color(self.color_theme["white"]),
            pos,
            self.drone_radius,
            width=1
            )

    def _draw_hud(
            self,
            now: float,
            end_turn: float,
            paused: bool = True
    ) -> None:
        """Bottom bar: turn counter, state and the playback menu."""
        if self.font is None:
            return
        if self.hud_font is None:
            self.hud_font = self._load_font(14)

        top = self.window_h - self.hud_height
        pygame.draw.rect(
            self.screen,
            pygame.Color(self.color_theme["bg-secondary"]),
            pygame.Rect(0, top, self.window_w, self.hud_height),
        )
        pygame.draw.line(
            self.screen,
            pygame.Color(self.color_theme["secondary"]),
            (0, top),
            (self.window_w, top),
        )

        end_turn_int = max(0, int(end_turn))
        turn = min(int(now) + 1, end_turn_int) if end_turn_int else 0
        title = self.font.render(
            f"Turn {turn}/{end_turn_int}",
            True,
            pygame.Color(self.color_theme["primary"]),
        )
        self.screen.blit(title, (self.padding, top + 6))

        state_text = "PAUSED" if paused else "PLAYING"
        state_color = (
            self.color_theme["warning"] if paused
            else self.color_theme["primary"]
        )
        state = self.font.render(
            state_text, True, pygame.Color(state_color))
        state_rect = state.get_rect()
        state_rect.midright = (
            self.window_w - self.padding,
            top + 6 + title.get_height() // 2,
        )
        pygame.draw.rect(
            self.screen,
            pygame.Color(self.color_theme["black"]),
            state_rect.inflate(16, 6),
            border_radius=6,
        )
        self.screen.blit(state, state_rect)

        self._draw_menu(top + 6 + title.get_height() + 6)

        bar = pygame.Rect(
            self.padding,
            self.window_h - 6,
            self.window_w - 2 * self.padding,
            3,
        )
        pygame.draw.rect(
            self.screen, pygame.Color(self.color_theme["black"]), bar)
        if end_turn_int:
            progress = min(max(now / end_turn_int, 0.0), 1.0)
            filled = bar.copy()
            filled.width = int(bar.width * progress)
            pygame.draw.rect(
                self.screen,
                pygame.Color(self.color_theme["primary"]),
                filled,
            )

    def _draw_menu(self, y: int) -> None:
        """Draw the clickable ``[KEY] action`` buttons.

        Every button is recorded in ``self.hud_buttons`` so the event loop
        can turn a click into the matching ``Command``.
        """
        font = self.hud_font
        mouse = pygame.mouse.get_pos()
        self.hud_buttons = []

        entries = []
        for key, label, command in HUD_CONTROLS:
            key_width = font.size(key)[0] + 10
            width = key_width + 6 + font.size(label)[0] + 12
            entries.append((key, label, command, key_width, width))

        # Shrink the gaps on a narrow window before dropping any option.
        gap = 10
        available = self.window_w - 2 * self.padding
        overflow = (sum(entry[4] for entry in entries)
                    + gap * (len(entries) - 1) - available)
        if overflow > 0:
            gap = max(4, gap - overflow // max(1, len(entries) - 1))

        height = font.get_height() + 10
        x = self.padding
        for key, label, command, key_width, width in entries:
            rect = pygame.Rect(x, y, width, height)
            if rect.right > self.window_w - self.padding:
                break

            hovered = rect.collidepoint(mouse)
            pygame.draw.rect(
                self.screen,
                pygame.Color(self.color_theme["black"]),
                rect,
                border_radius=6,
            )
            pygame.draw.rect(
                self.screen,
                pygame.Color(
                    self.color_theme["primary"] if hovered
                    else self.color_theme["tertiary"]
                ),
                rect,
                width=1,
                border_radius=6,
            )

            badge = pygame.Rect(
                rect.x + 5, rect.y + 5, key_width, rect.height - 10)
            pygame.draw.rect(
                self.screen,
                pygame.Color(self.color_theme["secondary"]),
                badge,
                border_radius=4,
            )

            key_surface = font.render(
                key, True, pygame.Color(self.color_theme["bg"]))
            label_surface = font.render(
                label, True, pygame.Color(self.color_theme["white"]))
            self.screen.blit(
                key_surface,
                (badge.x + 5,
                 badge.centery - key_surface.get_height() // 2),
            )
            self.screen.blit(
                label_surface,
                (badge.right + 6,
                 rect.centery - label_surface.get_height() // 2),
            )

            self.hud_buttons.append((rect, command))
            x = rect.right + gap

    def _command_at(self, pos: tuple[int, int]) -> Command | None:
        """Return the command of the menu button under ``pos``."""
        for rect, command in self.hud_buttons:
            if rect.collidepoint(pos):
                return command
        return None

    def _load_font(self, size: int = 20) -> Any:
        """Load the bundled Roboto Mono, falling back to a system font."""
        pygame.font.init()
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "static", "RobotoMono.ttf")
        if os.path.exists(path):
            return pygame.font.Font(path, size)
        return pygame.font.SysFont("monospace", size)
