from enum import Enum

from model.constants import ZONE_NAME_REGEXP
from model.zone import Zone


class ZoneColor(Enum):
    NONE = "none"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    WHITE = "white"
    BLACK = "black"
    BROWN = "brown"


class ZoneType(Enum):
    NORMAL = "normal"
    PRIORITY = "priority"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class Connection:
    def __init__(
            self,
            src: Zone,
            dest: Zone,
            link_capacity: int = 1
            ):
        self.src = src
        self.dest = dest
        self.link_capacity = link_capacity
