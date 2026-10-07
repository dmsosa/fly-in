from typing import Any

from model import Zone


class ZoneParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ZoneParser():

    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    @staticmethod
    def parse(data_str: str) -> dict[str, Any]:
        zone_type, tokens = data_str.split(":", 1)
        tokens_len = len(tokens)
        if tokens_len != 2:
            raise ZoneParseError(f"Invalid metadata line for zone '{tokens}'.")
        zone_name = zone_name.strip(": ")
        zone_data = {
            "name": zone_name,
            "coord": None,
            "zone_type": "normal",
            "color": None,
            "max_occupancy": 1
        }
        tokens = tokens.strip(" ").split(" ")
        try:
            zone_data["coord"] = (int(tokens[1]), int(tokens[2]))
        except ValueError:
            raise ZoneParseError(
                f"Zone {zone_data['name']} received invalid \
                coordinates: ({tokens[1]}, {tokens[2]})"
                )
        if tokens_len == 4:
            last_token = tokens[-1]
            valid_metadata = last_token[0] == "[" and last_token[-1] == "]"
            if valid_metadata:
                metadata = last_token.strip("[]")
                metadata_tokens = metadata.split(" ")
                for token in metadata_tokens:
                    parts = token.split("=")
                    if len(parts) != 2:
                        raise ZoneParseError(f"Invalid metadata token '{token}'.")
                    key, value = parts
                    if key == "color":
                        zone_data["color"] = value
                    elif key == "max_drones":
                        zone_data["max_occupancy"] = value
                    elif key == "zone":
                        zone_data["zone_type"] = value
                    else:
                        raise ZoneParseError(f"Metadata key for zone '{key}' not recognized.")
    
        return zone_data