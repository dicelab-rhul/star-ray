""" Defines 'active' component classes : [Component], [Actuator], [Sensor]. An active component is one that makes requests to the environment (actions) to sense (in the case of sensors) and to act (in the case of actuators). Sensing and acting are tied to the agents event cycle which is typically managed by the environment execution scheduler. See also 'passive' components TODO link. """

from __future__ import annotations
from typing import Type, Callable, Any
from collections import defaultdict
from functools import lru_cache
from functools import wraps
from typing import List, TYPE_CHECKING

from .component import Component
from ...event import Event
from ...pubsub import Subscriber, Subscribe, Unsubscribe

if TYPE_CHECKING:
    from ..agent import Agent
    from ...environment.ambient import _Ambient

__all__ = ("Sensor",)

# TODO self._actions behaviour is a bit weird
# sense actions should last until the end of the CURRENT __cycle__.
# act action should last until the end of the NEXT __cycle__.
# self._actions should be cleared at the END of each cycle.


class Sensor(Component, Subscriber):

    def __query__(self, state: _Ambient) -> None:
        # get sense actions
        actions = self.__sense__()
        assert isinstance(actions, (list, tuple))
        self._actions.extend(actions)
        self._actions = list(filter(None, self._actions))

        # set the source of these actions to this sensor
        Component.set_action_source(self, self._actions)
        # attempt the sense act and get the resulting observations
        observations = state.__select__(self._actions)
        # preprocess the observations ready to be received by the agent
        self._observations.push_all(self.__transduce__(observations))
        # clear sense actions ready for the next execution cycle
        self._actions.clear()

    def __notify__(self, message: Event) -> None:
        self._observations.push_all(self.__transduce__([message]))

    def __subscribe__(self) -> List[Subscribe]:
        """Subscription actions for this `Sensor`, these actions will be taken on the first call to `__query__`. During the lifetime of this `Sensor` subscription actions can be taken in the usual way as with any other action.

        Returns:
            List[Subscribe]: list of `Subscribe` actions to take. 

        Example:
            TODO
        """
        return []

    def on_add(self, agent: Agent) -> None:
        super().on_add(agent)
        self._actions.extend(self.__subscribe__())
        Sensor.set_subscriber(self, self._actions)

    def __sense__(self) -> List[Event]:
        """This method can be overridden to create a `Sensor` that does not depend on calls to `attempt` methods. This is useful if the `Sensor` should always sense the same kind of data.

        The default implementation of this method returns any actions that are given by the `attempt` methods implemented by this sensor.

        __Example__:
        ```
        class MySensor(Sensor):
            def __sense__(self):
                # new actions should always be created, do not re-use events!
                return [GetPosition()]
        ```

        See also:
            [`Actuator.__attempt__`]
        """
        return []

    @staticmethod
    def set_subscriber(sensor: Sensor, actions: List[Subscribe | Unsubscribe]):
        """ Sets the subscriber to the given sensor sensor if it is None for each action in actions.

        Args:
            sensor (Sensor): sensor to use as the subscriber.
            actions (List[Subscribe  |  Unsubscribe]): action for which to set `subscriber` attribute.
        """
        for action in actions:
            if action.subscriber is None:
                # TODO this will currently call __notify__ of the agent... not this sensor!
                # it only works locally at the moment
                action.subscriber = sensor
