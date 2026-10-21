from typing import Any
from pydantic import BaseModel, Field
import pygame
from model import FlyinGraph
from orchestrator.orchestrator import Move
from orchestrator.reservation_table import ReservationTable


class FlyinPygameGui(BaseModel):
    """
    Graphical User Interface for Fly-in
    """
    graph = FlyinGraph
    zone_width: int = Field(default=15, ge=10)
    zone_height: int = Field(default=5, ge=5)
    metadata_height: int = Field(default=2, ge=2)
    margin: int = Field(default=10)

    def model_post_init(self, _context: Any) -> None:
        self.all_zones = (
            [self.graph.start_zone] + [self.graph.end_zone] + self.graph.zones
        )

        all_x_coords = [zone.coord[0] for zone in self.graphall_zones]
        all_y_coords = [zone.coord[1] for zone in self.graphall_zones]
        self.max_x = max(all_x_coords)
        self.min_x = min(all_x_coords)
        self.max_y = max(all_y_coords)
        self.min_y = min(all_y_coords)

        #  Step 2: Compute the extent (width/height) of that box
        range_x = self.max_x - self.min_x or 1
        range_y = self.max_y - self.min_y or 1
        # The or 1 guards against division by zero if all zones
        # share the same x or y
        # (degenerate case — all in a line or a single point).
        scale_x = (self.width - 2 * self.padding) / range_x
        scale_y = (self.height - 2 * self.padding) / range_y
        self.scale = min(scale_x, scale_y)
        pass

        def draw_graph(self) -> None:
            pass

        def print_history(self, history: list[list[Move]], reservations: ReservationTable) -> None:
            """simple loop"""
            clock = pygame.time.Clock()
            current_time = 0.0
            turns_per_second = 2.5
            max_turn = max([zone_occupancy[1] for zone_occupancy in reservations.zone_occupancy.keys()])
            pygame.font.init()
            font = pygame.font.SysFont('./static/RobotoMono.ttf', 22)

            running = True
            while running:
                dt = clock.tick(60) / 1000.0
                # Handling pygame events like key pressings
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            current_time = 0.0
                        if event.key == pygame.K_ESCAPE:
                            running = False

                if current_time < max_turn:
                    current_time += dt * turns_per_second
                self.screen.fill(pygame.Color("black"))
                self.draw_graph()

                for drone_id, path in self.drone_paths.items():
                    px, py = self.get_drone_pixel_pos(path, current_time)
                    self.draw_drone_glow(px, py, glow_color=(
                        255, 255, 255), glow_radius=16, alpha=75)

                for drone_id, path in self.drone_paths.items():
                    px, py = self.get_drone_pixel_pos(path, current_time)
                    pygame.draw.circle(self.screen, pygame.Color(
                        "black"), (px, py), radius=6)
                    pygame.draw.circle(self.screen, pygame.Color(
                        "white"), (px, py), radius=6, width=1)

                esc_text = font.render("Press ESC to quit",
                                    True, pygame.Color("#ffffff"))
                space_text = font.render(
                    "Press SPACE to reset", True, pygame.Color("#ffffff"))
                self.screen.blit(esc_text, (20, self.height - 50))
                self.screen.blit(space_text, (20, self.height - 25))

                pygame.display.flip()
            pygame.quit()
