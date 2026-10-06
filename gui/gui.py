from typing import Any, Optional
from pydantic import BaseModel, Field
from gui.constants import UX_STD
from model import FlyinGraph
from model.graph import Zone
from menu import FlyinMenu
from .utils import UX_MAX, exit_program


DELAY: float = 0.5
FAST: float = 0.1
DIRECT: float = 0.0


class FlyinGui(BaseModel):
    """
    Graphical User Interface for Fly-in
    """
    graph: FlyinGraph
    all_zones: list[Zone] = Field(default_factory=list)
    zone_width: int = Field(default=15, ge=10)
    zone_height: int = Field(default=5, ge=5)
    metadata_height: int = Field(default=2, ge=2)
    margin: int = Field(default=10)
    row: Optional[int] = Field(default=None, ge=0)
    col: Optional[int] = Field(default=None, ge=0)

    def model_post_init(self, __context: Any) -> None:
        self.all_zones = (
            [self.graph.start_zone] + [self.graph.end_zone] + self.graph.zones
        )

        all_x_coords = [zone.coords[0] for zone in self.all_zones]
        all_y_coords = [zone.coords[1] for zone in self.all_zones]
        max_x = max(all_x_coords)
        min_x = min(all_x_coords)
        max_y = max(all_y_coords)
        min_y = min(all_y_coords)

        self.min_x = min_x
        self.min_y = min_y

        width = (max_x - min_x + 1) * self.zone_width + self.margin * 2
        height = (max_y - min_y + 1) * (
            self.zone_height + self.metadata_height
        ) + self.margin * 2

        self.col, self.row = width, height
        pass

    
    def confirm_map_file(self, map_name: str, menu: "FlyinMenu") -> bool:
        """Prompts the user to review and confirm the loaded map.

        Args:
            gui (Gui): Interface containing the rendered map.
            map_name (str): Chosen map identifier.

        Returns:
            bool: True if confirmed, False to return to map selection.
        """
        print("Do you want to continue?")
        col = self.col if self.col < UX_MAX else UX_STD
        print("\n" + "═" * col)
        print("pLEASE CONFIRM THE MAP")
        print("═" * col, end="\n\n")
        print(f"Using following: {map_name}\n")

        if self.col < UX_MAX:
            print("grid")
        else:
            print("size warning")
        idx = menu.run_confirm_file_map()

        if idx == 0:
            return True
        if idx == 1:
            return False
        else:
            exit_program()

        return False