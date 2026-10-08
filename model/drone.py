from enum import Enum, auto
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


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
    start_zone: str
    end_zone: str
    current_zone: Optional[str] = Field(default=None)
    target_zone: Optional[str] = Field(default=None)
    move_count: int = Field(default=0)

    def begin_move(self, to: str) -> None:
        self.current_zone = None
        if to.max_capacity == to.drone_count:
            self.state = DroneState.WAIT
        else:
            self.state = DroneState.FLYING
