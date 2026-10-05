from gui.utils import ERROR
from model.drone import Connection, Zone


class ConnectionParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ConnectionParser():

    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    @staticmethod
    def parse(data_str: str) -> Connection:
        tokens = data_str.split(" ")
        tokens_len = len(tokens)
        if tokens_len < 1 or tokens_len > 2:
            raise ConnectionParser(ERROR["parser"]["connections"]["parsing_line"].format(data_str))
        zone_names = tokens[0].split("-")
        if len(zone_names != 2):
            raise ConnectionParseError(ERROR["parser"]["connections"]["zone_names"].format(zone_names))
        zone_a = zone_names[0]
        zone_b = zone_names[1]
        if tokens_len == 2:
            last_token = tokens[-1]
            valid_metadata = last_token[0] == "[" and last_token[-1] == "]"
            if valid_metadata:
                metadata = tokens[-1].strip("[]")
                metadata_tokens = metadata.split(" ")
                max_link_capacity = None
                for token in metadata_tokens:
                    parts = token.split("=")
                    if len(parts) != 2:
                        raise ConnectionParser(ERROR["parser"]["metadata_token"].format(token))
                    key, value = parts
                    if key == "max_link_capacity":
                        max_link_capacity = value
                    else:
                        raise ConnectionParser(ERROR["parser"]["connections"]["metadata_key"].format(key))
            else:
                raise ConnectionParseError(ERROR["parser"]["metadata_format"].format(last_token))
        conn = Connection(zone_a, zone_b, max_link_capacity)
        return conn