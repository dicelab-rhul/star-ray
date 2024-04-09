from abc import abstractmethod, ABC
import uuid
from typing import List, Set
from .component import Sensor, Actuator, Component
from ..utils import DictObservable, int64_uuid


class AgentFactory(ABC):

    @abstractmethod
    def __call__(self, *args, **kwargs) -> ABC:
        pass


class Agent(ABC):
    def __init__(
        self, sensors: List[Sensor], actuators: List[Actuator], *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._id = int64_uuid()
        self._sensors = set()
        self._actuators = set()
        for sensor in sensors:
            self.add_component(sensor)
        for actuator in actuators:
            self.add_component(actuator)

        if len(self.sensors) != len(sensors) or len(self.actuators) != len(actuators):
            print(len(self.sensors), len(sensors))
            print(len(self.actuators), len(actuators))

            raise TypeError(
                "Components were not added to this agent upon initialisation, did you override `add_component` and forget to call super()?"
            )

    @property
    def sensors(self) -> Set:
        return set(self._sensors)

    def get_sensors(self) -> Set:
        return set(self._sensors)

    @property
    def actuators(self) -> Set:
        return set(self._actuators)

    def get_actuators(self) -> Set:
        return set(self._actuators)

    @property
    def id(self) -> int:
        return self._id

    def get_id(self) -> int:
        return self._id

    # TODO type hints _State
    def __sense__(self, state, *args, **kwargs):
        _ = [sensor.__query__(state) for sensor in self.sensors]

    # TODO type hints _State
    def __execute__(self, state, *args, **kwargs):
        _ = [actuator.__query__(state) for actuator in self.actuators]

    def add_component(self, component: Component):
        if isinstance(component, Sensor):
            self._sensors.add(component)
        elif isinstance(component, Actuator):
            self._actuators.add(component)
        else:
            raise TypeError(f"Unsupported component type: {type(component)}")

    def remove_component(self, component: Component):
        if isinstance(component, Sensor):
            self._sensors.remove(component.id)
        elif isinstance(component, Actuator):
            self._actuators.remove(component.id)
        else:
            raise TypeError(f"Unsupported component type: {type(component)}")

    @abstractmethod
    def __cycle__(self):
        pass

    # TODO remove in favour of __kill__
    def kill(self):
        self.__kill__()

    def __kill__(self):
        pass
