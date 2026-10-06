from enum import Enum, auto
from git import Optional
from pydantic import BaseModel, ConfigDict, Field
from .graph import Zone


class DroneState(Enum):
    FLYING = auto()
    WAIT = auto()
    STOP = auto()


class Drone(BaseModel):
    """
        This class represents a drone, which has methods:
        fields:
        - current zone
        - target zone
        - final zone
        - id: str


        - begin_move(to: Zone)
        - finish_move(self)
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    state: DroneState = Field(default=DroneState.STOP)
    start: Optional[Zone] = Field(default=None)
    end: Optional[Zone] = Field(default=None)
    current_zone: Optional[Zone] = Field(default=None)
    target: Optional[Zone] = Field(default=None)
    move_count: int = Field(default=0)

    def begin_move(self, to: Zone) -> None:
        self.current_zone = None
        if to.max_capacity == to.drone_count:
            self.status = DroneState.WAIT
        self.state = DroneState.FLYING
