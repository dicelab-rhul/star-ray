"""Module defines the decorator `@attempt`.

The `@attempt` decorator should be used on methods that are meant to take actions in `Actuator` and `Sensor` components. It is also used in the automatic routing of actions to relevant components as implemented in the `AgentRouted` class. See these classes and the `attempt` documentation for details.
"""

from functools import wraps
from ...utils import TypeRouter

__all__ = ("attempt",)


def attempt(*event_types: list[type]):
    """A decorator that defines an `attempt` method within a `Component`. `attempt` methods should be called in the agent's `__cycle__` method to schedule an action for execution. This is true of both actuators and sensors.

    Args:
        event_types (List[Type]): A list of types that the decorated `Component` method will receive if event routing is enabled. If this is not specified then an attempt will be made to discover the types via the type hint of the first argument of the decorated function.

    Sensors: `Sensor` actions will be attempted at the start of the next cycle (before the next `__cycle__` is called).
    Actuators: `Actuator` actions will be attempted at the end of the agents current cycle (after `__cycle__` has finished).

    For an action the properly scheduled for execution it must be returned by the decorated method (see example below).

    Example:
    ```
    class MyActuator(Actuator):
        @attempt
        def move(self, direction):
            return MoveAction(direction)


    class MyAgent(Agent):
        def __cycle__(self):
            # the action will be executed after __cycle__ is finished.
            self.actuators[0].move("EAST")
    ```


    """

    def _attempt(func, route_types=None):
        if route_types is None:
            route_types = TypeRouter.resolve_first_argument_types(
                func, allow_no_arguments=True
            )
        else:
            route_types = TypeRouter.resolve_route_types(route_types)

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            action = func(self, *args, **kwargs)
            if isinstance(action, list | tuple):
                self._actions.extend(action)
            else:
                self._actions.append(action)
            return action

        # used to identify whether a given method has been decorated with this decorator.
        wrapper.is_attempt = True
        # this is used to automatically route events to a given component.
        if route_types:
            route_types = TypeRouter.validate_route_types(func, route_types)
            wrapper.route_types = route_types
        return wrapper

    if len(event_types) == 0:
        return _attempt
    elif len(event_types) == 1 and isinstance(event_types[0], list | tuple):

        def _wrap(func, route_types=event_types[0]):
            return _attempt(func, route_types=route_types)

        return _wrap
    elif len(event_types) == 1:
        # event_types is actually the function we are wrapping... used the decorator as @attempt without arguments
        return _attempt(event_types[0], route_types=None)
    else:
        raise ValueError(
            "Decorator `@attempt` takes a single positional argument `event_types`."
        )
