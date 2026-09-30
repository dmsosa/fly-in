import re
from typing import TypeAlias

Coord: TypeAlias = tuple[int, int]


ZONE_NAME_REGEXP = re.compile(r"^[A-Za-z0-9]+$")
ZONE_COLOR_REGEXP = re.compile(r"^[a-z]+$")
