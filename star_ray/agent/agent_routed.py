from typing import List
from functools import wraps
import inspect

from .component import Sensor, Actuator
from .component.type_routing import _TypeRouter
from .agent import Agent


def _component_arg(func):
    kwargs = list(inspect.signature(func).parameters.keys())
    if "component" in kwargs:
        return func
    else:
        @wraps(func)
        def _wrapped(*args, **_):
            return func(*args)
        return _wrapped


class AgentRouted(Agent):
    _TYPE_ROUTER_CACHE_SIZE = 1024

    def __init__(
        self, sensors: List[Sensor], actuators: List[Actuator], *args, **kwargs
    ):
        super().__init__(sensors, actuators, *args, **kwargs)
        self._observe_router = _TypeRouter(
            cache_size=AgentRouted._TYPE_ROUTER_CACHE_SIZE)
        # get all methods and add them to the observe router
        for method in _TypeRouter.get_all_decorated_methods(self):
            self._observe_router.add(_component_arg(method))
        # NOTE: dynamically added method will not be called by the router...

    def __cycle__(self):
        self.__observe__()

    def __observe__(self):
        for actuator in self.get_actuators():
            for observation in actuator.iter_observations():
                self._observe_router(observation, component=actuator)
        for sensor in self.get_sensors():
            for observation in sensor.iter_observations():
                self._observe_router(observation, component=sensor)
