from typing import Any, Optional
from pydantic import BaseModel, Field
from model import FlyinGraph, Zone
from menu import FlyinMenu
from orchestrator.orchestrator import Move
from .utils import exit_program
from .constants import UX_MAX, \
UX_STD


DELAY: float = 0.5
FAST: float = 0.1
DIRECT: float = 0.0


class FlyinGui:
    """
    Graphical User Interface Ascii for Fly-in
    """
    graph: FlyinGraph
    history: list[list[Move]]

    def model_post_init(self, __context: Any) -> None:
        self.all_zones = (
            [self.graph.start_zone] + [self.graph.end_zone] + self.graph.zones
        )

        all_x_coords = [zone.coord[0] for zone in self.all_zones]
        all_y_coords = [zone.coord[1] for zone in self.all_zones]
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