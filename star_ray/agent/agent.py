from abc import abstractmethod, ABCMeta
import uuid
from typing import List
from .component import Sensor, Actuator


class Agent(metaclass=ABCMeta):
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

    def sense(self, sensor):
        pass

    def execute(self, actuator):
        pass

    def __sense__(self, ambient):
        _ = [self.sense(sensor) for sensor in self.sensors]
        _ = [sensor.__query__(ambient) for sensor in self.sensors]

    def __execute__(self, ambient):
        _ = [self.execute(actuator) for actuator in self.actuators]
        _ = [actuator.__query__(ambient) for actuator in self.actuators]

    @abstractmethod
    def __cycle__(self):
        pass

    def kill(self):
        pass
