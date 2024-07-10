from typing import List, Dict, Any, Callable, Type
from functools import wraps
import inspect

from ..event import Event
from .component import Component

from .component import Sensor, Actuator
from .component.type_routing import _TypeRouter
from .agent import Agent


def _get_decide_methods(obj: Any):
    methods = inspect.getmembers(obj, predicate=inspect.ismethod)
    return [m[1] for m in filter(lambda x: getattr(x[1], "is_decide", False), methods)]


def _component_arg(func):
    kwargs = list(inspect.signature(func).parameters.keys())
    if "component" in kwargs:
        return func
    else:
        @wraps(func)
        def _wrapped(*args, **kwargs):
            del kwargs['component']
            return func(*args, **kwargs)
        return _wrapped


def decide(*fun):
    def _decide(func):
        func.is_decide = True
        return func

    if len(fun) == 0:
        return _decide
    elif len(fun) == 1:
        return _decide(fun[0])
    else:
        raise ValueError("`decide` decorator takes no arguments.")


class AgentRouted(Agent):

    _TYPE_ROUTER_CACHE_SIZE = 64

    def __init__(
        self, sensors: List[Sensor], actuators: List[Actuator], *args, **kwargs
    ):
        # this may be added to in super().__init__, these will route actions to the relevent actuators
        self._attempt_routers: Dict[int, _TypeRouter] = dict()

        super().__init__(sensors, actuators, *args, **kwargs)
        self._observe_router = _TypeRouter(
            cache_size=AgentRouted._TYPE_ROUTER_CACHE_SIZE)

        # these methods are those that have been decorated with @observe, they will recieve observations of the relevant type from the sensors.
        self._observe_methods = list(filter(lambda m: getattr(m, "is_observe", False),
                                            _TypeRouter.get_all_decorated_methods(self)))
        for method in self._observe_methods:
            self._observe_router.add(_component_arg(method))
        # TODO: dynamically added methods will not be called by the router... perhaps we need a way to add new ones?

        # these methods are those that have been decorated with @decide, they are to be called in `__cycle__`.
        self._decide_methods = _get_decide_methods(self)

    def add_observe_method(self, func: Callable, event_types: List[Type]):
        func = _component_arg(func)  # handle optional "component" argument
        self._observe_methods.append(func)
        self._observe_router.add(func, event_types)

    def attempt(self, action: Event | List[Event], component: Component = None):
        """ Manually attempt one or more actions. 

        If `component` is not provided, this method will search for the relevant component(s) to attempt the `action` based on its type using the usual action routing mechanism (see `AgentRouted`).

        Args:
            action (Event | List[Event]): action (or actions) to attempt.
            component (Component, optional): to attempt with. Defaults to None.
        """
        if not isinstance(action, (list, tuple)):
            action = (action,)
        if component is None:
            for attempt_router in self._attempt_routers.values():
                for a in filter(None, action):
                    attempt_router(a)

        else:
            attempt_router = self._attempt_routers[component.id]
            for a in filter(None, action):
                attempt_router(a)

    def add_component(self, component: Component) -> Component:
        component = super().add_component(component)
        # get attempt methods from the component (if any) and register them with a new _TypeRouter
        attempt_methods = list(filter(lambda m: getattr(m, "is_attempt", False),
                                      _TypeRouter.get_all_decorated_methods(component)))
        if len(attempt_methods) > 0:
            attempt_router = _TypeRouter(
                cache_size=AgentRouted._TYPE_ROUTER_CACHE_SIZE)
            for method in attempt_methods:
                attempt_router.add(method)
            self._attempt_routers[component.id] = attempt_router
        else:
            pass  # no attempt methods were defined
        return component

    def remove_component(self, component: Component) -> Component:
        component = super().remove_component(component)
        if component.id in self._attempt_routers:
            del self._attempt_routers[component.id]
        return component

    def __cycle__(self):
        self.__observe__()
        self.__decide__()

    def __decide__(self):
        resulting_actions = []
        for method in self._decide_methods:
            # the method is already bound
            decisions = method()
            if not isinstance(decisions, (list, tuple)):
                decisions = [decisions]
            # forward the actions to the relevant actuators
            for decision in filter(None, decisions):
                for attempt_router in self._attempt_routers.values():
                    action = attempt_router(decision)
                    resulting_actions.append(action)
        return resulting_actions  # TODO do something with these?

    def __observe__(self):
        for actuator in self.get_actuators():
            for observation in actuator.iter_observations():
                print(observation)
                assert isinstance(observation, Event)
                self._observe_router(observation, component=actuator)
        for sensor in self.get_sensors():
            for observation in sensor.iter_observations():
                assert isinstance(observation, Event)
                self._observe_router(observation, component=sensor)
