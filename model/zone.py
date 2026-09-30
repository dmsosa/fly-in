from enum import Enum

from model.constants import ZONE_NAME_REGEXP, ZONE_COLOR_REGEXP


class ZoneType(Enum):
    NORMAL = "normal"
    PRIORITY = "priority"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class Zone:
    def __init__(
            self,
            x: int,
            y: int,
            name: str = "none",
            color: str = "none",
            zone_type: str = "normal"
            ):
        if not ZONE_NAME_REGEXP.match(name):
            raise ValueError(
                f"Invalid name for zone: {name}. "
                "It must be alphanumeric and "
                "do not contain dashes '-' or special characters."
                )
        if not ZONE_COLOR_REGEXP.match(color):
            raise ValueError(
                f"Invalid color for zone: {name}. "
                "It must be a single-word string "
                )
        if zone_type not in [t.value for t in ZoneType]:
            raise ValueError(f"Invalid type for zone: {zone_type}")
        self.name = name
        self.color = color
        self.zone_type = zone_type
        self.x = x
        self.y = y
