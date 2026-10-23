from dataclasses import dataclass
import os
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from gui.constants import THEME_COLOR
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
DRONE_RADIUS = 4
ANIM_DURATION = 1.0

@dataclass
class DroneAnim:
    zone: str                        # logical zone it is in / heading to
    from_px: tuple[float, float]     # where the segment starts
    to_px: tuple[float, float]       # where it ends
    t0: float                        # turn-time the segment started
    duration: float = ANIM_DURATION # turns


class FlyinPygameGui(BaseModel):
    """
    Graphical User Interface for Fly-in
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    graph: FlyinGraph
    drones: dict[str, Drone]
    reservations: ReservationTable
    padding: int = Field(default=50)
    min_x: int = Field(default=1)
    max_x: int = Field(default=1)
    min_y: int = Field(default=1)
    max_y: int = Field(default=1)
    color_theme: dict[str, Any] = THEME_COLOR
    turns_per_second: float = Field(default=1.0, gt=0)
    drone_radius: int = Field(default=DRONE_RADIUS, ge=1)
    anim_duration: float = Field(default=ANIM_DURATION, gt=0)
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
    drone_anims: dict[str, DroneAnim] = Field(default_factory=dict, exclude=True)

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

        self._init_drone_animations()

    def to_pixel(self, x: int, y: int) -> tuple[int, int]:
        px = self.offset_x + (x - self.min_x) * self.scale
        py = self.offset_y + (y - self.min_y) * self.scale
        return int(px), int(py)

    def _init_drone_animations(self) -> None:
        start_px = self.to_pixel(*self.graph.start_zone.coord)
        self.drone_anims = {
            drone_id: DroneAnim(
                self.graph.start_zone.name,
                start_px,
                start_px,
                0.0
            )
            for drone_id in self.drones
        }

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
            pygame.draw.circle(
                self.screen,
                pygame.Color(self.color_theme["tertiary"]),
                (px, py),
                radius=17
                )
            pygame.draw.circle(
                self.screen,
                pygame.Color(color),
                (px, py),
                radius=15
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

    def print_history(self, history: list[list[Move]]) -> None:
        """
        simple loop
        The standard Pygame loop order is:

        Handle events (pygame.event.get())
        Update game logic (using dt)
        Draw / render
        clock.tick(60)
        """
        self._init_drone_animations()
        self.font = self._load_font()
        clock = pygame.time.Clock()
        current_time = 0.0
        turns_per_second = 1.0 / self.turns_per_second
        current_turn = 0
        end = float(len(history))
        turn_count = len(history)
        pygame.font.init()
        running = True
        paused = False
        while running:
            dt = clock.tick(60) / 1000.0 # Seconds passed since last frame
            # current time determines actually in which turn we are placed on
            if current_turn == turn_count:
                running = False
            if current_time < end:
                if manual:
                    self.
                current_time = min(end, current_time + dt / turns_per_second)
            # Handling pygame events like key pressings
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        current_time = 0.0
                        current_turn = 0
                        self._init_drone_animations()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_p:
                        paused = not paused
                    else:
                        key = event.unicode
                        if key in ("W", "left_arrow"):
                            current_turn = max(0, current_turn - 2)
                            current_time = max(0, current_time - 1)
                        elif key in ("S", "right_arrow"):
                            current_turn = min(turn_count, current_turn + 1)
                            current_time = min(turn_count, current_time + 1)
                        elif key in ("S", "right_arrow"):
                            current_turn = min(turn_count, current_turn + 1)
                            current_time = min(turn_count, current_time + 1)
                        # qu'est que ce passe se on ne actualise pas les positions des animations?
                        # ca que se passe, est que les px sont elles encore
                        # turn count is 6, current time is 5.44
                        # turn is 5, curent time is 4.44
                        # le trn de cheque animation etancore
                        # la meme,donc la progression serai toujours 1, au moins que
                        # n a reduit le num de current_time suffisement pour simulair un  progres plus petit.
                        # mais la position do origin et destination serant tojours la meme.
                        # donc, c'est necessaire de reduir le current tunr pour le duble?

            if not paused:
                while current_turn < turn_count and current_time >= current_turn:
                    self._update_anim_info(history, current_turn)
                    current_turn += 1

                self.screen.fill(pygame.Color(self.color_theme["bg"]))
                self.draw_graph()

                for anim in self.drone_anims.values():
                    px, py = self._get_drone_pixels(anim, current_time)
                    # But the progress depend on how many seconds have passed
                    self._draw_drone(px, py)

                self._draw_hud(current_time, turn_count)

            pygame.display.flip()

        pygame.quit()

    def _update_anim_info(
            self,
            history: list[list[Move]],
            current_turn: int,
            ) -> None:
            turn = history[current_turn]
            for move in turn:
                anim = self.drone_anims.get(move.drone_id, None)
                
                if anim is None:
                    continue

                anim.t0 = current_turn
                target_name = move.target_name
                if "-" in target_name:
                    parts = target_name.split("-")
                    origin, dest = parts
                else:
                    origin = anim.zone
                    dest = target_name

                origin_zone = self.graph.get_zone_by_name(origin)
                dest_zone = self.graph.get_zone_by_name(dest)

                anim.zone = dest_zone.name

                px1, py1 = self.to_pixel(*origin_zone.coord)
                px2, py2 = self.to_pixel(*dest_zone.coord)

                anim.from_px = px1, py1
                anim.to_px = (px2, py2)

    def _get_drone_pixels(
            self,
            anim: DroneAnim,
            current_time: float,
            ) -> tuple[float, float]:
            p = current_time - anim.t0 / (anim.t0 + 1 - anim.t0)
            p = max(0.0, min(1.0, p))

            x1, y1 = anim.from_px[0], anim.from_px[1]
            x2, y2 = anim.to_px[0], anim.to_px[1]

            px = x1 + (x2 - x1) * p
            py = y1 + (y2 - y1) * p

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
            total_turns: int,
            paused: bool = True
    ) -> None:
        """Show the current turn and the controls at the bottom."""
        if self.font is None:
            return

        turn = min(int(now) + 1, total_turns)
        hud_surface = pygame.Surface((500, 250))
        hud_surface.fill((0,0,255))

        label = self.font.render(
            f"Turn {turn}/{total_turns}",
            True,
            pygame.Color(self.color_theme["primary"]),
        )

        paused_label = self.font.render(
            f"PAUSED",
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
        self.screen.blit(hud_surface, (0, 0))
        self.screen.blit(label, (self.offset_x + self.padding, y))
        self.screen.blit(
            hint, (self.window_w - hint.get_width() - self.padding, y))
        if paused:
            self.screen.blit(paused_label, (self.window_w // 2, self.window_h // 2))
#  mantenaint, cettee idee n'est pas complete parce il faut aussi actualise les donness de cheque animation
# pour ca, on doit programmer un facon pour bien comprendre ce sujet. on doit a
