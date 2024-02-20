from typing import Optional, Any

from star_ray.agent import Agent
from star_ray.typing import Event, QueryXPath

from dataclasses import dataclass, astuple


@dataclass
class MATBIIQuery(Event):

    element_id: str
    state: Optional[Any] = None

    @staticmethod
    def update_warning_light1(source: str):
        return MATBIIQuery(
            *astuple(Event.new(source)), element_id=ID_LIGHT1, state=None
        )

    @staticmethod
    def update_warning_light2(source: str):
        return MATBIIQuery(
            *astuple(Event.new(source)), element_id=ID_LIGHT2, state=None
        )


class MATBIIAgent(Agent):

    def __init__(self, sensors, actuators):
        super().__init__(sensors, actuators)

    def __cycle__(self):
        pass
