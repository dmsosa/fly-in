from typing import Any

from model import Connection


class ConnectionParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ConnectionParser():

    def __init__(self) -> None:
        """Start with nothing selected."""
        pass

    @staticmethod
    def parse(data_str: str) -> dict[str, Any]:
        tokens = data_str.split(" ")
        tokens_len = len(tokens)
        
        if tokens_len < 1:
            raise ConnectionParseError(f"Invalid metadata line for connection '{data_str}'.")
        zone_names = tokens[0].split("-")
        if len(zone_names) != 2:
            raise ConnectionParseError(f"Invalid metadata zone names for connection '{zone_names}'.")
        
        conn_data = {
            "zone_a": zone_names[0],
            "zone_b": zone_names[1],
            "max_link_capacity": None,
        }
        
        if tokens_len > 1:
            for metadata in tokens[1:]:
                parts = metadata.split("=")
                if len(parts) != 2:
                    raise ConnectionParseError(f"Invalid metadata token '{metadata}'.")
                meta_key, meta_value = parts
                meta_key = meta_key.strip("[]")
                meta_value = meta_value.strip("[]")
                        
                if meta_key == "max_link_capacity":
                    if conn_data["max_link_capacity"] is not None:
                        raise ConnectionParseError(f"Metadata duplicated '{meta_key}'.")
                    try:
                        conn_data[meta_key] = int(meta_value)
                    except ValueError:
                        raise ConnectionParseError(f"Metadata value for 'max_link_capacity' is not valid '{meta_value}'.")
                else:
                    raise ConnectionParseError(f"Metadata key for connection '{meta_key}' not recognized.")

        if conn_data["max_link_capacity"] is None:
            conn_data["max_link_capacity"] = 1
    
        return conn_data