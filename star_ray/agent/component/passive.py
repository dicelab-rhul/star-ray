from typing import Type
from abc import abstractmethod
from .component import Component, Sensor, Actuator
from star_ray import Event


class PassiveComponent(Component):

    @abstractmethod
    def subscribe(self, event: Type):
        pass

    @abstractmethod
    def publish(self, event: Event):
        pass


class PassiveActuator(PassiveComponent, Actuator):
    pass


class PassiveSensor(PassiveComponent, Sensor):
    pass
