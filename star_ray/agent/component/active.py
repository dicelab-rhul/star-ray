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

    @staticmethod
    def attempt(fun):
        """A decorator that defines an `attempt` method in this component. `attempt` methods should be called in the agent's `__cycle__` method to schedule an action for execution. This is true of both actuators and sensors.
        Sensors:
            Any [`ActiveSensor`] actions will be attempted at the start of the next cycle (before the next `__cycle__` is called).
        Actuators:
            Any [`ActiveActuator`] actions will be attempted at the end of the agents current cycle (after `__cycle__` has finished).

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

        @wraps(fun)
        def wrapper(self, *args, **kwargs):
            action = fun(self, *args, **kwargs)
            self._actions.append(action)  # pylint: disable=W0212
            return action

        return wrapper


class ActiveSensor(ActiveComponent, Sensor):

    def __query__(self, state: _State):
        self._actions = self.__sense__()  # see the __sense__ method.
        self._observations = state.select(self._actions)
        self._actions.clear()

    def __sense__(self) -> List[Event]:
        """This method can be overriden to create a sensor that does not depend on calls to `attempt` methods. This is useful if the sensor should always request the same __kind__ of data.

        The default implementation of this method simply returns any actions returned by an `attempt` methods.

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

    @staticmethod
    def attempt(fun):
        return ActiveComponent.attempt(fun)


class ActiveActuator(ActiveComponent, Actuator):

    def __query__(self, state: _State):
        self._actions = self.__attempt__()
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

    @staticmethod
    def attempt(fun):
        return ActiveComponent.attempt(fun)
