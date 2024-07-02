""" Defines 'active' component classes : [Component], [Actuator], [Sensor]. An active component is one that makes requests to the environment (actions) to sense (in the case of sensors) and to act (in the case of actuators). Sensing and acting are tied to the agents event cycle which is typically managed by the environment execution scheduler. See also 'passive' components TODO link. """

from __future__ import annotations
from typing import List, TYPE_CHECKING

from .component import Component
from ...event import Event
from ...pubsub import Subscriber, Subscribe, Unsubscribe

if TYPE_CHECKING:
    from ...environment.wrapper_state import State

__all__ = ("Sensor",)

# TODO self._actions behaviour is a bit weird
# sense actions should last until the end of the CURRENT __cycle__.
# act action should last until the end of the NEXT __cycle__.
# self._actions should be cleared at the END of each cycle.


class Sensor(Component, Subscriber):

    def __query__(self, state: State) -> None:
        # get sense actions
        self._actions = self.__sense__()
        # set the source of these actions to this sensor
        self._set_source(self._actions)
        # attempt the sense act and get the resulting observations
        observations = state.__select__(self._actions)
        # preprocess the observations ready to be received by the agent
        self._observations.push_all(self.__transduce__(observations))
        # clear sense actions ready for the next execution cycle
        self._actions.clear()

    def __notify__(self, message: Event):
        self._observations.push(message)

    def __subscribe__(self) -> List[Subscribe | Unsubscribe]:
        return []

    def __initialise__(self, state: State) -> None:
        self._actions = self.__subscribe__()
        self._set_subscriber(self._actions)
        if self._actions:
            self._set_source(self._actions)
            observations = state.__subscribe__(self._actions)
            self._observations.push_all(self.__transduce__(observations))
            self._actions.clear()

    def _set_subscriber(self, actions: List[Subscribe | Unsubscribe]):
        # set the subscriber to this sensor if it is None
        for action in actions:
            if action.subscriber is None:
                action.subscriber = self

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
