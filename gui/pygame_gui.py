from dataclasses import dataclass
import math
import os
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from gui.constants import THEME_COLOR
from gui.game_loop import GameLoop, Replay, key_commands, poll_events
from model import FlyinGraph
from model.drone import Drone
from orchestrator.orchestrator import Move
from orchestrator.reservation_table import ReservationTable


os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


FPS = 60
HUD_HEIGHT = 80
ZONE_RADIUS = 15
DRONE_RADIUS = 8
ANIM_DURATION = 1.0


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
    hud_height: int = Field(default=HUD_HEIGHT, ge=1)

    # Runtime state. Pydantic v2 crashes if we set attributes
    # that are not declared as fields. So every value created in 
    # model_post_init (or later) needs a field here.
    screen: Any = Field(default=None, exclude=True)
    font: Any = Field(default=None, exclude=True)
    scale: float = Field(default=0.0, exclude=True)
    offset_x: float = Field(default=0.0, exclude=True)
    offset_y: float = Field(default=0.0, exclude=True)
    window_w: int = Field(default=0, exclude=True)
    window_h: int = Field(default=0, exclude=True)
    timelines: dict[str, list[Segment]] = Field(default_factory=dict, exclude=True)

    def model_post_init(self, _context: Any) -> None:
        if not PYGAME_AVAILABLE:
            raise ImportError(
                "Error: Pygame is not installed. " \
                "GUI can not run"
                )

        pygame.init()

        # Get desktop resolution BEFORE set_mode
        info = pygame.display.Info()

        # 75% of monitor width
        self.window_w = int(info.current_w * 0.75)
        self.window_h = int(info.current_h * 0.75)  # or a fixed height if you prefer

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

        usable_w  = (self.window_w - 2 * inset_x) 
        usable_h = (self.window_h - 2 * inset_y) - self.hud_height

        scale_x = usable_w // range_x
        scale_y = usable_h // range_y

        self.scale = min(scale_x, scale_y)

        # X coordinate needs to start from the left, but not
        # from the left of the entire window size, but
        # from the left of the area used for drawing the graph
        # and also taking into account the padding with 2 * padding
        self.offset_x = inset_x + (
            usable_w - range_x * self.scale) // 2
        self.offset_y = inset_y + (
            usable_h - range_y * self.scale) // 2

        self._build_timeline()

    def to_pixel(self, x: int, y: int) -> tuple[int, int]:
        px = self.offset_x + (x - self.min_x) * self.scale
        py = self.offset_y + (y - self.min_y) * self.scale
        return int(px), int(py)

    def draw_graph(self) -> None:
        """Draws the connections and zones on the screen"""
        for conn in self.graph.connections:
            name_a, name_b = conn.get_zone_names()
            zone_a = self.graph.get_zone_by_name(name_a)
            zone_b = self.graph.get_zone_by_name(name_b)
            x1, y1 = zone_a.coord
            x2, y2 = zone_b.coord
            p1 = self.to_pixel(x1, y1)
            p2 = self.to_pixel(x2, y2)

            is_high_capacity = conn.max_link_capacity > 1
            if is_high_capacity:
                color = self.color_theme["connection-primary"]
            else:
                color = self.color_theme["connection-secondary"]
            self.draw_connection(
                p1, p2,
                color=pygame.Color(color),
                thickness=min(5, max(1, conn.max_link_capacity)),
                dashed=not is_high_capacity
            )

        for zone in self.graph.all_zones:
            px, py = self.to_pixel(zone.coord[0], zone.coord[1])

            if zone.color:
                try:
                    hex_code = self.color_theme.get(zone.color, self.color_theme["secondary"])
                    color = pygame.Color(hex_code)
                except ValueError:
                    color = pygame.Color(self.color_theme["secondary"])
            else:
                color = pygame.Color(self.color_theme["secondary"])
            capacity = zone.max_drones if zone.max_drones else math.inf
            is_high_capacity = capacity > 3
            if is_high_capacity:
                radius = self.zone_radius
            else:
                radius = self.zone_radius + 3
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

    def draw_connection(
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

    def _find_slots(self, drone_to_zone: dict[str, str]) -> dict[str, tuple[int, int]]:
        place_members: dict[str, list[str]] = {}
        for drone_id, place_name in drone_to_zone.items():
            place_members.setdefault(place_name, []).append(drone_id)

        slots: dict[str, tuple[int, int]] = {}
        for drones_in_place in place_members.values():
            for idx, drone_id in enumerate(sorted(drones_in_place)):
                slots[drone_id] = (idx, len(drones_in_place))
        return slots
    
    def _zone_center(self, zone_name: str) -> tuple[float, float]:
        zone = self.graph.get_zone_by_name(zone_name)
        
        x, y = zone.coord
        px, py = self.to_pixel(
            x,
            y
            )
        
        return (px, py)

    def _offset_pixels(self, zone_name: str, slot: int, max_slot: int) -> tuple[float, float]:
        if "-" in zone_name:                       # a link → point along the segment
            name_a, name_b = zone_name.split("-", 1)
            ax, ay = self._zone_center(name_a)
            bx, by = self._zone_center(name_b)
            f = (slot + 1) / (max_slot + 1)       # 1/2 alone, 1/3 & 2/3 for two
            return ax + (bx - ax) * f, ay + (by - ay) * f

        cx, cy = self._zone_center(zone_name)
        if max_slot <= 1:                         # a lone drone sits in the middle
            return cx, cy

        ring = self.zone_radius - self.drone_radius // 2
        angle = 2 * math.pi * slot / max_slot - math.pi / 2

        return cx + ring * math.cos(angle), cy + ring * math.sin(angle)
    
    def _find_slot(self, zone_name: str, idx: int, max_idx: int) -> tuple[int, int]:
        pass

    def _build_timeline(self) -> None:
        start = self.graph.start_zone.name
        timelines: dict[str, list[Segment]]  = {
            drone_id: [] for drone_id in self.drones.keys()
        }

        drone_to_zone = {drone_id: start for drone_id in self.drones.keys()}
    
        # each turn appends a new segment for each drone
        for turn_id, turn in enumerate(self.history):
            start_of_turn = dict(drone_to_zone) # snapshot

            for move in turn:
                # if this drone moved, append its objective to the goal
                drone_that_moved = move.drone_id
                drone_to_zone[drone_that_moved] = move.target_name

            start_of_turn_slots = self._find_slots(start_of_turn)
            end_of_turn_slots = self._find_slots(drone_to_zone)

            for drone_id, timeline in timelines.items():
                # Drone can end on the middle of a connection
                # after having tried to access a restricted zone
                origin_name = start_of_turn[drone_id]
                dest_name = drone_to_zone[drone_id]

                from_px = self._offset_pixels(origin_name, *start_of_turn_slots[drone_id])
                to_px = self._offset_pixels(origin_name, *end_of_turn_slots[drone_id])
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
        """
        self.font = self._load_font()
        clock = pygame.time.Clock()
        pygame.font.init()
        keymap = key_commands()
        loop = GameLoop(
            end=float(len(self.history)),
            turns_per_second=self.turns_per_second
            )

        while loop.running:
            dt = clock.tick(self.fps) / 1000.0 # Seconds passed since last frame
            # current time determines actually in which turn we are placed on
            loop.handle(poll_events(keymap))
            loop.advance(dt)
            # Handling pygame events like key pressings

            if not loop.paused:
                self._render(loop)



            pygame.display.flip()

        pygame.quit()

    def _render(self, replay: Replay) -> None:
        # if my current turn is , I need to iterate through each drone, in the segment number 0
        self.screen.fill(pygame.Color(self.color_theme["bg"]))
        self.draw_graph()
        for drone_id in self.timelines.keys():
            px, py = self._get_drone_pixels(replay.now, drone_id)
            self._draw_drone(px, py)

        self._draw_hud(replay.now, replay.end, replay.paused)

    def _get_drone_pixels(
            self,
            current_time: float,
            drone_id: str
            ) -> tuple[float, float]:
        timeline = self.timelines[drone_id]
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
                pygame.Color(self.color_theme["green"]),
                pos,
                self.drone_radius
            )            
            pygame.draw.circle(
                self.screen,
                pygame.Color(self.color_theme["info"]),
                pos,
                self.drone_radius,
                width=1
                )

    def _load_font(self) -> Any:
        """Load the bundled Roboto Mono, falling back to a system font."""
        pygame.font.init()
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "static", "RobotoMono.ttf")
        if os.path.exists(path):
            return pygame.font.Font(path, 20)
        return pygame.font.SysFont("monospace", 20)

    def _draw_hud(
            self,
            now: float,
            end_turn: float,
            paused: bool = True
    ) -> None:
        """Show the current turn and the controls at the bottom."""
        if self.font is None:
            return

        end_turn_int = int(end_turn)
        turn = min(int(now) + 1, end_turn_int)
        hud_surface = pygame.Surface((500, 250))
        hud_surface.fill((0,0,255))

        label = self.font.render(
            f"Turn {turn}/{end_turn_int}",
            True,
            pygame.Color(self.color_theme["primary"]),
        )

        paused_label = self.font.render(
            "PAUSED",
            True,
            pygame.Color(self.color_theme["primary"]),
        )

        options = [
            {
                "key": "W",
                "label": "One turn back",
            }
        ]
        hint = self.font.render(
            "ESC to quit", True, pygame.Color("#ffffff"))

        y = self.window_h - HUD_HEIGHT + 16
        hud_surface.blit(label, (self.offset_x + self.padding, y))
        hud_surface.blit(
            hint, (self.window_w - hint.get_width() - self.padding, y))
        self.screen.blit(hud_surface, (0, 0))
        if paused:
            self.screen.blit(paused_label, (self.window_w // 2, self.window_h // 2))
#  mantenaint, cettee idee n'est pas complete parce il faut aussi actualise les donness de cheque animation
# pour ca, on doit programmer un facon pour bien comprendre ce sujet. on doit a
