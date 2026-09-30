from model.zone import Zone


class ConnectionParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ConnectionParser():

    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    @staticmethod
    def parse(tokens: list[str]) -> Zone:
        first_token = tokens[0][-1]
        tokens_len = len(tokens)
        if tokens_len != 3 and tokens_len != 2:
            raise ConnectionParser("Invalid parse line")
        if first_token != "connection":
            raise ConnectionParser("Invalid connection")
        zone_names = tokens[1].split("-")
        if len(zone_names != 2):
            raise ConnectionParseError(f"Invalid connection zone_names: {zone_names}")
        from_name = zone_names[0]
        to_name = zone_names[1]
        last_token = tokens[-1]
        has_metadata = last_token[0] == "[" and last_token[-1] == "]"
        if has_metadata:
            metadata = tokens[-1].strip("[]")
            metadata_tokens = metadata.split(" ")
            max_link_capacity = None
            for data in metadata_tokens:
                parts = data.split("=")
                if len(parts) != 2:
                    raise ConnectionParser("Invalid metadata line for zone")
                key, value = parts
                if key == "max_link_capacity":
                    max_link_capacity = value
                else:
                    raise ConnectionParser("Invalid key metadata for zone")
        from_zone = graph.zone_by_name[from_name]
        to_zone = graph.zone_by_name[to_name]
        conn = Connection(from_zone, to_zone, max_link_capacity)
        return new_zone