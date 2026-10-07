from pydantic import BaseModel, ConfigDict, Field

from src.model.drone import Drone
from src.model.graph import FlyinGraph


class Orchestrator(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    turn_count: int = Field(ge=0)
    graph: FlyinGraph
    drones: set[Drone] = Field(default_factory=set)

    def model_post_init(self, __context) -> None:
        self.drones = self.graph.start_zone.drones

    def start_orchestra(self) -> None:
        end_zone = self.graph.end_zone
        total_drones = self.graph.drones_count
        while end_zone.drone_count < total_drones:
            for d in self.drones:
                links_available = [] 
                current_zone = d.current_zone
                for link in current_zone.links:
                    opposite_zone = link.get_opposite(current_zone.name)
                    if opposite_zone.type == ZoneType.RESTRICTED:
                        continue
                    occupancy_cost = opposite_zone.get_occupancy
                    
