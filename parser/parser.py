import math
from pathlib import Path
from typing import Any
from .connection_parser import ConnectionParser
from .zone_parser import ZoneParseError, ZoneParser
from error import FlyinParseError


class FlyinParser:
    """
    Parser is going to build a dictionary without caring about the actual values
    and pass them to the corresponding Pydantic Models for more complex validation
    once a Zone is sucessfully created, you can pass the entire dictionary to the
    parent pydantic model "Graph"

    Graph of zones (vertices) and connections (edges).
    fields:
    drone_count # number of drones the graph contains
    start_zone # starting zone for all drones
    end_zone # goal zone for all drones
    zones # all zones in a set
    connections # all connections in a set
    """

    """Holds the level, file name and final path of the map to load."""
    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    def _valid_key(self, key: str) -> bool:
        return key == "nb_drones" \
                or key == "hub" \
                or key == "start_hub" \
                or key == "end_hub" \
                or key == "connection"

    def parse(self, file_path: str | Path) -> dict[str, Any]:
        """
        This function receives the file_path after the user interacted with the menu
        then reads the file and builds the flyin graph.

        Handles all file-related exceptions
        """        
        with open(file_path, 'r') as f:
            filename = Path(file_path).stem
            print(f"Trying to read the map file: {filename}...")
            lines = f.readlines()

            if not lines:
                raise FlyinParseError("Config file is empty")
            print("File open successful: OK.")

        result_dict = {
            "filename": filename,
            "drone_count": None,
            "start_zone": None,
            "end_zone": None,
            "zones": [],
            "connections": [],
        }

        first_line_nb_drones = False

        for row, l in enumerate(lines):
            l = l.strip()

            if not l or l.startswith("#"):
                continue

            parts = l.split(":", 1)

            if len(parts) != 2:
                raise FlyinParseError(f"Bad key:value format received: Line {row + 1}")

            key, data = parts
            key = key.strip().lower()
            data = data.strip()

            if not first_line_nb_drones and key != "nb_drones":
                raise FlyinParseError(f"The first line must define the number of drones using nb_drones: <number>.")
            
            if not self._valid_key(key):
                raise FlyinParseError(f"Key for parser not recognized: '{key}'. [Line: {row + 1}]")

            if key == "hub":
                zone_data = ZoneParser.parse(data)
                zone_data["hub_type"] = "hub"
                result_dict["zones"].append(zone_data)
            elif key == "start_hub":
                if result_dict["start_zone"] is not None:
                    raise FlyinParseError(f"There must be exactly one start_hub. [Line: {row + 1}]")
                zone_data = ZoneParser.parse(data)
                zone_data["hub_type"] = "start"
                zone_data["max_drones"] = None
                result_dict["start_zone"] = zone_data
            elif key == "end_hub":
                if result_dict["end_zone"] is not None:
                    raise FlyinParseError(f"There must be exactly one end_hub. [Line: {row + 1}]")
                zone_data = ZoneParser.parse(data)
                zone_data["hub_type"] = "end"
                zone_data["max_drones"] = None
                result_dict["end_zone"] = zone_data
            elif key == "connection":
                conn = ConnectionParser.parse(data)
                result_dict["connections"].append(conn)
            elif key == "nb_drones":
                if result_dict["drone_count"] is not None:
                    msg = "" \
                        f"Not valid configuration file {file_path}\n" \
                        f"The 'nb_count' option was defined more than once.\n" \
                        f"   └── first value was: {result_dict['drone_count']}" \
                        f"   └── [Line {row + 1}]" \
                    ""
                    raise FlyinParseError(msg)
                try:
                    value = int(data)
                    result_dict["drone_count"] = value
                    first_line_nb_drones = True
                except ValueError:
                    raise FlyinParseError(f"Invalid value for drone count: '{data}'. [Line {row + 1}]")
    
        if not result_dict["start_zone"]:
            raise FlyinParseError("Mandatory key for parser is missing: 'start_hub'.")
        if not result_dict["end_zone"]:
            raise FlyinParseError("Mandatory key for parser is missing: 'end_hub'.")
        if not result_dict["drone_count"]:
            raise FlyinParseError("Mandatory key for parser is missing: 'nb_drones'.")

        return result_dict
