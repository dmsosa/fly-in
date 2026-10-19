from collections import deque
from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .graph import Zone, Connection


class DroneState(Enum):
    FLYIN = auto()
    WAIT = auto()
    STOP = auto()
    DELIVERED = auto()


# How many recently visited zones the drone remembers. Used to break
# short cycles (ping-pong) without pinning the drone forever: old entries
# fall out of the window as the drone keeps moving.
VISITED_MEMORY = 3


class Drone(BaseModel):
    """
    Autonomous agent in the flight network.

    The orchestrator decides *where* the drone goes and owns every
    capacity reservation. The drone only holds its own bookkeeping:
    where it is, what it is heading to, and the last few zones it visited
    so that the orchestrator can steer it away from short cycles.
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    state: DroneState = Field(default=DroneState.STOP)
    current_zone: Optional[Zone] = Field(default=None)
    target: Optional[Zone] = Field(default=None)
    connection: Optional[Connection] = Field(default=None)
    last_visited: deque[str] = Field(
        default_factory=lambda: deque(maxlen=VISITED_MEMORY)
    )
    wait_count: int = Field(default=0, ge=0)
    move_count: int = Field(default=0, ge=0)

    def add_last_visited(self, zone_name: str) -> None:
        """Record that the drone just arrived in ``zone_name``."""
        self.last_visited.append(zone_name)

    def has_visited(self, zone_name: str) -> bool:
        """True while ``zone_name`` is still in the drone's memory window."""
        return zone_name in self.last_visited
