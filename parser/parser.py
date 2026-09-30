from parser.connection_parser import ConnectionParser
from parser.zone_parser import ZoneParser

from ..error import FlyinParseError
from parser.utils import valid_line
from ..model.graph import FlyinGraph




class FlyinParser:
    """Holds the level, file name and final path of the map to load."""

    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    @staticmethod
    def parse(file_path: str, graph: "FlyinGraph") -> None:
        """
        This function receives the file_path after the user interacted with the menu
        then reads the file and builds the flyin graph.

        Handles all file-related exceptions
        """
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for l in lines:
                if l.startswith("#"):
                    continue
                if len(l) < 1:
                    continue
                tokens = l.split(" ")
                first_token = tokens[0][:-1]
                if not valid_line(first_token):
                    raise FlyinParseError(f"Not valid configuration file {file_path}")
                if first_token == "hub" \
                    or first_token == "start_hub" \
                        or first_token == "end_hub":
                    new_zone = ZoneParser.parse(l)
                    graph.add_zone(new_zone)
                elif first_token == "connection":
                    conn = ConnectionParser.parse(l)
                    graph.add_connection(conn)
                elif first_token == "nb_drones":
                    value = l.split(":")[1]
                    if graph.drone_count is not None:
                        raise FlyinParseError(f"Not valid configuration file {file_path}\nThe nb_count option is received more than once.\nGraph has defined {graph.drone_count} and received {value}")
                else:
                    raise FlyinParseError(f"Unkown key detected while parsing: {first_token}")
