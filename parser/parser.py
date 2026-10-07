from pathlib import Path
from typing import Any
from .connection_parser import ConnectionParser
from .zone_parser import ZoneParser
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
            file_path_str = str(file_path)
            filename = file_path_str.split('/')[-1].removesuffix(".txt")
            print(f"Trying to read the map file: {filename}...")
            lines = f.readlines()
            if not lines:
                raise FlyinParseError("Config file is empty")
            print("OK")

        result_dict = {
            "filename": filename,
            "drone_count": None,
            "start_zone": None,
            "end_zone": None,
            "zones": [],
            "connections": [],
        }
        for row, l in enumerate(lines):
            l = l.strip()
            if not l or l.startswith("#"):
                continue

            key, data = l.lower().split(":", 1)
            key = key.strip()
            data = data.strip()
            if not self._valid_key(key):
                raise FlyinParseError(f"Key for parser not recognized: '{key}'. [Line: {row + 1}]")

            if key == "hub":
                new_zone = ZoneParser.parse(data)
                result_dict["zones"].append(new_zone)
            elif key == "start_hub":
                if result_dict["start_zone"] is not None:
                    raise FlyinParseError("There must be exactly one start_hub")
                new_zone = ZoneParser.parse(data)
                result_dict["start_zone"] = new_zone
            elif key == "end_hub":
                if result_dict["end_zone"] is not None:
                    raise FlyinParseError("There must be exactly one end_hub")
                new_zone = ZoneParser.parse(data)
                result_dict["end_zone"] = new_zone
            elif key == "connection":
                conn = ConnectionParser.parse(data)
                result_dict["connections"].append(conn)
            elif key == "nb_drones":
                try:
                    value = int(data)
                except ValueError:
                    raise ValueError(f"Invalid value for drone count: '{value}'")
                if result_dict["drone_count"] is not None:
                    msg = "" \
                        f"Not valid configuration file {file_path}\n" \
                        f"The nb_count option was defined more than once.\n" \
                        f"   └── {result_dict['nb_count']}, {value}" \
                        f"   └── [Line {row}]" \
                    ""
                    raise FlyinParseError(msg)
                result_dict["drone_count"] = value
    
        if not result_dict["start_zone"]:
            raise ValueError("Mandatory key for parser is missing: 'start_hub'.")
        if not result_dict["end_zone"]:
            raise ValueError("Mandatory key for parser is missing: 'end_hub'.")
        if not result_dict["drone_count"]:
            raise ValueError("Mandatory key for parser is missing: 'nb_drones'.")

        return result_dict
