from typing import Any
from pydantic import BaseModel, Field
from model import FlyinGraph


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
