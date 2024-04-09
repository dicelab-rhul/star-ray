from collections import defaultdict
from types import MethodType

from .agent import Agent
from .component import Actuator, Component


class RoutedActionAgent(Agent):

    def __init__(self, sensors, actuators, *args, **kwargs):
        # actions will be routed by type according to this map, it should not be modified manually.
        self._action_router_map = defaultdict(set)
        super().__init__(sensors, actuators, *args, **kwargs)

    def add_component(self, component: Component):
        super().add_component(component)
        if isinstance(component, Actuator):
            for (
                event_cls_name,
                method,
            ) in RoutedActionAgent.get_route_events(component):
                self._action_router_map[event_cls_name].add(method)

    def remove_component(self, component: Component):
        super().remove_component(component)
        if isinstance(component, Actuator):
            for (
                event_cls_name,
                method,
            ) in RoutedActionAgent.get_route_events(component):
                self._action_router_map[event_cls_name].remove(method)

    def __attempt__(self, actions):
        for action in actions:
            cls_name = _fully_qualified_name(action.__class__)
            attempts = self._action_router_map.get(cls_name, None)
            if attempts is None:
                raise ValueError(
                    f"Failed to find a suitable actuator to attempt action: {type(action)} during automatic routing."
                )
            for attempt in attempts:
                attempt(action)

    @staticmethod
    def get_route_events(*actuators):
        for actuator in actuators:
            for attempt in actuator.__class__.__attemptmethods__:
                route_events = attempt.route_events
                if route_events:
                    for event_cls in route_events:
                        yield _fully_qualified_name(event_cls), MethodType(
                            attempt, actuator
                        )


def _fully_qualified_name(cls):
    return cls.__module__ + "." + cls.__qualname__
