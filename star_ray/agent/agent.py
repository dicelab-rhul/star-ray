from abc import abstractmethod, ABC
from typing import List, Set
from .component import Sensor, Actuator, Component
from ..utils import int64_uuid


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
            raise TypeError(
                "Components were not added to this agent upon initialisation, did you override `add_component` and forget to call super()?"
            )

    @property
    def sensors(self) -> Set[Sensor]:
        return set(self._sensors)

    def get_sensors(self) -> Set[Sensor]:
        return set(self._sensors)

    @property
    def actuators(self) -> Set[Actuator]:
        return set(self._actuators)

    def get_actuators(self) -> Set[Actuator]:
        return set(self._actuators)

    @property
    def id(self) -> int:
        return self._id

    def get_id(self) -> int:
        return self._id

    def __initialise__(self, state):
        _ = [sensor.__initialise__(state) for sensor in self.sensors]
        _ = [actuator.__initialise__(state) for actuator in self.actuators]

    # TODO type hints State
    def __sense__(self, state, *args, **kwargs):
        _ = [sensor.__query__(state) for sensor in self.sensors]

    # TODO type hints State
    def __execute__(self, state, *args, **kwargs):
        _ = [actuator.__query__(state) for actuator in self.actuators]

    def add_component(self, component: Component) -> Component:
        if isinstance(component, Sensor):
            self._sensors.add(component)
        elif isinstance(component, Actuator):
            self._actuators.add(component)
        else:
            raise TypeError(f"Unsupported component type: {type(component)}")
        component.on_add(self)
        return component

    def remove_component(self, component: Component):
        if isinstance(component, Sensor):
            self._sensors.remove(component)
        elif isinstance(component, Actuator):
            self._actuators.remove(component)
        else:
            raise TypeError(f"Unsupported component type: {type(component)}")
        component.on_remove(self)

    @abstractmethod
    def __cycle__(self):
        pass

    # TODO remove in favour of __terminate__
    def kill(self):
        self.__terminate__()

    def __terminate__(self):
        pass
