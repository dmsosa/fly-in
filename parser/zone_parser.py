from gui.utils import ERROR
from model.drone import Zone


class ZoneParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ZoneParser():

    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    @staticmethod
    def parse(data_str: str) -> Zone:
        tokens = data_str.split(" ")
        tokens_len = len(tokens)
        if tokens_len < 1 or tokens_len > 4 or tokens_len < 3:
            raise ZoneParseError(f"Invalid metadata line for zone '{data_str}'.")
        name = tokens[0]
        try:
            coords = (int(tokens[1]), int(tokens[2]))
        except ValueError:
            raise ZoneParseError(
                f"Zone {name} received invalid \
                coordinates: ({tokens[1]}, {tokens[2]})"
                )
        if tokens_len == 4:
            last_token = tokens[-1]
            valid_metadata = last_token[0] == "[" and last_token[-1] == "]"
            if valid_metadata:
                metadata = last_token.strip("[]")
                metadata_tokens = metadata.split(" ")
                zone_type = None
                color = None
                max_drones = 1
                for token in metadata_tokens:
                    parts = token.split("=")
                    if len(parts) != 2:
                        raise ZoneParseError(f"Invalid metadata token '{token}'.")
                    key, value = parts
                    if key == "color":
                        color = value
                    elif key == "max_drones":
                        max_drones = value
                    elif key == "zone":
                        zone_type = value
                    else:
                        raise ZoneParseError(f"Metadata key for zone '{key}' not recognized.")
        
        new_zone = Zone(name, coords, color, zone_type, max_drones)
        
        return new_zone