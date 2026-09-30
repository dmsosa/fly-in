from model.zone import Zone


class ZoneParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ZoneParser():

    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    @staticmethod
    def parse(tokens: list[str]) -> Zone:
        first_token = tokens[0][-1]
        if len(tokens) != 5:
            raise ZoneParseError("Invalid parse line")
        if first_token != "hub":
            raise ZoneParseError("Invalid zone")
        is_start = first_token == "start_hub"
        is_end = first_token == "end_hub"
        name = tokens[1]
        coords = (tokens[2], tokens[3])
        metadata = tokens[-1].strip("[]")
        metadata_tokens = metadata.split(" ")
        for data in metadata_tokens:
            parts = data.split("=")
            if len(parts) != 2:
                raise ZoneParseError("Invalid metadata line for zone")
            zone_type = None
            color = None
            max_drones = 1
            key, value = parts
            if key == "color":
                color = value
            elif key == "max_drones":
                max_drones = value
            elif key == "zone":
                zone_type = value
            else:
                raise ZoneParseError("Invalid key metadata for zone")
        new_zone = Zone(name, coords, color, zone_type, max_drones, is_start, is_end)
        return new_zone