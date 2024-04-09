from __future__ import annotations  # make type hints work :)
from typing import List, TYPE_CHECKING

from abc import abstractmethod
from functools import wraps

from ...event import Event

from .component import Component, Sensor, Actuator

from ..wrapper_observations import _Observations

if TYPE_CHECKING:
    from ...environment.wrapper_state import _State


class ActiveComponent(Component):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # actions to attempt in the current cycle
        self._actions: List[Event] = []
        # observations that result from self._actions
        self._observations: _Observations = _Observations.empty()

    def get_observations(self) -> List[Event]:
        # we should be consuming these here....
        return list(self._observations)

    @abstractmethod
    def __query__(self, state: _State):
        """Calling this method will cause this [`ActiveComponent`] to query the state of the environment.
        This should not be called manually, it will be called by the environment execution scheduler.
        """

    def _set_source(self, actions):
        for action in actions:
            # TODO or perhaps we should use the id of the agent?
            if action.source is None:
                action.source = self.id


class ActiveSensor(ActiveComponent, Sensor):

    def __query__(self, state: _State):
        self._actions = self.__sense__()  # see the __sense__ method.
        self._set_source(self._actions)
        self._observations = state.select(self._actions)
        self._actions.clear()

    def __sense__(self) -> List[Event]:
        """This method can be overriden to create a sensor that does not depend on calls to `attempt` methods. This is useful if the sensor should always request the same __kind__ of data.

        The default implementation of this method returns any actions returned by `attempt` methods implemented by this sensor.

        Example:
        ```
        class PositionSensor(ActiveSensor):
            def __sense__(self):
                # new actions should always be created, do not re-use events!
                return [QueryAgentPosition()]
        ```
        See also:
            [`ActiveActuator.__attempt__`]
        """
        return self._actions


class ActiveActuator(ActiveComponent, Actuator):

    def __query__(self, state: _State):
        self._actions = self.__attempt__()
        self._set_source(self._actions)
        self._observations = state.update(self._actions)
        self._actions.clear()

    def __attempt__(self):
        """This method can be overriden to create an actuator that does not depend on calls to `attempt` methods. This is useful if the actuator should always perform the same kind of action independently of the agents decision making.

        The default implementation of this method simply returns any actions returned by an `attempt` methods.

        Example:
        ```
        class FowardActuator(ActiveActuator):
            def __attempt__(self):
                # new actions should always be created, do not re-use events!
                return [QueryMoveForward()]
        ```
        See also:
            [`ActiveSensor.__sense__`]
        """
        return self._actions


def attempt(*fun, route_events=None):
    """A decorator that defines an `attempt` method within a [Component]. `attempt` methods should be called in the agent's `__cycle__` method to schedule an action for execution. This is true of both actuators and sensors.
    Sensors:
        Any [`ActiveSensor`] actions will be attempted at the start of the next cycle (before the next `__cycle__` is called).
        TODO [PassiveSensor]

    Actuators:
        Any [`ActiveActuator`] actions will be attempted at the end of the agents current cycle (after `__cycle__` has finished).
        TODO [PassiveActuator]

    Args:
        fun ([`Callable`]): a function to wrap.

    Example:
    ```
    class MyActuator(ActiveActuator):

        @Actuator.attempt
        def move(self, direction):
            return MoveAction(direction)

    class MyAgent(Agent):
        def __cycle__(self):
            # the action will be executed after __cycle__ is finished.
            self.actuators[0].move("EAST")
    ```
    """

    def _attempt(func, route_events=route_events):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            action = func(self, *args, **kwargs)
            if isinstance(action, (list, tuple)):
                self._actions.extend(action)  # pylint: disable=W0212
            else:
                self._actions.append(action)  # pylint: disable=W0212
            return action

        # used to identify whether a given method has been decorated with this decorator.
        wrapper.is_attempt = True
        # this is used to automatically route events to a given component.
        if not route_events is None:
            route_events = _validate_route_events(fun, route_events)
        wrapper.route_events = route_events
        return wrapper

    if len(fun) == 0:
        return _attempt
    elif len(fun) == 1:
        return _attempt(fun[0])
    else:
        raise ValueError(
            f"Invalid arguments: {fun}, should contain only function to decorate, use keyword arguments otherwise."
        )


def _validate_route_events(fun, route_events):
    def _get_message():
        return f"`attempt` decorator received invalid arguments for fun {fun}:"

    # validate the routes provided
    if not isinstance(route_events, (list, tuple)):
        raise ValueError(_get_message(), "`route_events` must be a list or tuple.")
    if len(route_events) == 0:
        raise ValueError(_get_message(), "`route_events` must not be empty.")
    for cls in route_events:
        if not isinstance(cls, type):
            raise ValueError(
                _get_message(),
                f"`route_events` must contain only types but received {cls}",
            )
    return list(route_events)