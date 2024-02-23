from typing import Optional, Any

from star_ray.agent import Agent
from star_ray.typing import Event, QueryXPath, QueryXMLTemplated

from dataclasses import dataclass, astuple


class MATBIIAgent(Agent):

    def __init__(self, sensors, actuators):
        super().__init__(sensors, actuators)

    def __cycle__(self):
        pass
