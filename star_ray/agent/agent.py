from abc import abstractmethod, ABC
import uuid
from typing import List
from .component import Sensor, Actuator


class AgentFactory(ABC):

    @abstractmethod
    def new(self) -> ABC:
        pass


class Agent(ABC):
    def __init__(
        self, sensors: List[Sensor], actuators: List[Actuator], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._id = str(uuid.uuid4())
        self.sensors = sensors
        self.actuators = actuators

    @property
    def id(self):
        return self._id

    def __sense__(self, ambient, *args, **kwargs):
        _ = [sensor.__query__(ambient) for sensor in self.sensors]

    def __execute__(self, ambient, *args, **kwargs):
        _ = [actuator.__query__(ambient) for actuator in self.actuators]

    @abstractmethod
    def __cycle__(self):
        pass

    def kill(self):
        pass

    def get_id(self):
        return self.id
