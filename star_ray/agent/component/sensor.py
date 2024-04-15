""" Defines 'active' component classes : [Component], [Actuator], [Sensor]. An active component is one that makes requests to the environment (actions) to sense (in the case of sensors) and to act (in the case of actuators). Sensing and acting are tied to the agents event cycle which is typically managed by the environment execution scheduler. See also 'passive' components TODO link. """

from __future__ import annotations  # make type hints work :)
from typing import Any, List, TYPE_CHECKING

from ...event import Event

from .component import Component

from ...pubsub import Subscriber

if TYPE_CHECKING:
    from ...environment.wrapper_state import _State


__all__ = ("Sensor",)


class Sensor(Component, Subscriber):

    def __query__(self, state: _State) -> None:
        # get sense actions
        self._actions = self.__sense__()
        # set the source of these actions to this sensor
        self._set_source(self._actions)
        # attempt the sense act and get the resulting observations
        observations = state.select(self._actions)
        # preprocess the observations ready to be received by the agent
        self._observations.push_all(self.__transduce__(observations))
        # clear sense actions ready for the next execution cycle
        self._actions.clear()

    def __notify__(self, message: Event):
        self._observations.push(message)

    def __sense__(self) -> List[Event]:
        """This method can be overriden to create a sensor that does not depend on calls to `attempt` methods. This is useful if the sensor should always request the same kind of data.

        The default implementation of this method returns any actions that are given by the `attempt` methods implemented by this sensor.

        Example:
        ```
        class MySensor(Sensor):
            def __sense__(self):
                # new actions should always be created, do not re-use events!
                return [GetPosition()]
        ```
        It is also possible to combine this with `attempt` using the `iter_actions()` method.
        Example 2:
        ```
        class MySensor(Sensor):

            @attempt
            def turn(self):
                return GetDirection()

            def __sense__(self):
                return [GetPosition(), *self.iter_actions()]
        ```

        See also:
            [`Actuator.__attempt__`]
        """
        return self._actions
