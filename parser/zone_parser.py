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
        tokens = data_str.strip().split(" ")
        tokens_len = len(tokens)
        if tokens_len < 3 or not tokens[0]:
            raise ZoneParseError(f"Invalid metadata line for zone '{tokens}'.")
        
        try:
            zone_name = tokens[0]
            coord = (int(tokens[1]), int(tokens[2]))
        except ValueError:
            raise ZoneParseError(
                f"Zone {zone_data['name']} received invalid \
                coordinates: ({tokens[1]}, {tokens[2]})"
                )
        
        zone_data = {
            "name": zone_name,
            "coord": coord,
            "type": None,
            "color": None,
            "max_drones": None
        }

        if tokens_len > 3:
            for metadata in tokens[3:]:
                parts = metadata.split("=")
                if len(parts) != 2:
                    raise ZoneParseError(f"Invalid metadata token '{metadata}'.")
                meta_key, meta_value = parts
                meta_key = meta_key.strip("[]")
                meta_value = meta_value.strip("[]")
                        
                if meta_key == "max_drones":
                    if zone_data["max_drones"] is not None:
                        raise ZoneParseError(f"Metadata duplicated '{meta_key}'.")
                    try:
                        zone_data[meta_key] = int(meta_value)
                    except ValueError:
                        raise ZoneParseError(f"Metadata value for 'max_drones' is not valid '{meta_value}'.")
                elif meta_key == "color":
                    if zone_data["color"] is not None:
                        raise ZoneParseError(f"Metadata duplicated '{meta_key}'.")
                    zone_data[meta_key] = meta_value
                elif meta_key == "zone":
                    if zone_data["type"] is not None:
                        raise ZoneParseError(f"Metadata duplicated '{meta_key}'.")
                    zone_data["type"] = meta_value
                else:
                    raise ZoneParseError(f"Metadata key for zone '{meta_key}' not recognized.")

        if zone_data["type"] is None:
            zone_data["type"] = "normal"
        if zone_data["max_drones"] is None:
            zone_data["max_drones"] = 1

        return zone_data