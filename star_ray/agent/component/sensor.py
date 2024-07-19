"""Module defining the `Sensor` class. See class documentation for details."""

from __future__ import annotations
from typing import TYPE_CHECKING

from .component import Component
from ...event import Event
from ...pubsub import Subscriber, Subscribe, Unsubscribe

if TYPE_CHECKING:
    from ..agent import Agent
    from ...environment import State

__all__ = ("Sensor",)


class Sensor(Component, Subscriber):
    """Base class for a sensor. `Sensors`s may be attached to an `Agent` and will allow them to "sense" the current state of the environment. A sensor does this by taking "sense actions", which are read only actions. sense actions occur as part of `__sense__` in the agents cycle.

    Sensing often happens without an explicit decision made by the agent. The `__sense__` method can be overriden to continuously (once per cycle) take a set of sense actions.

    __Example__:
    ```
    class MySensor(Sensor):
        def __sense__(self):
            # new actions should always be created, do not re-use events!
            return [GetPositionAction()]
    ```

    These observations are then avaliable in the agents cycle via the `iter_observations` method.

    Example:
    ```
    class MyAgent(Agent):
        def __cycle__(self):
            for observation in self.my_sensor.iter_observations():
                print(observation)  # update beliefs or make decisions
    ```
    Note that `iter_observations` will consume the observations, more will not be avaliable until the next cycle (after the next round of sensing).

    Sensors may also take advance of `star_ray`s pub-sub mechanism (`Sensor` implements the `Subscriber` interface) and can subscribe to passively receive certain types of event. The `__subscribe__` method may be used for this purpose, it is called once automatically upon initialisation of the sensor (after it is has been attached to an agent) and should return a list of `Subscribe` actions. The sensors observations will then automatically be populated with any published data that it subscribed to. Note that it is up to the environment to define what data is made avaliable to a sensor (i.e. what `Publisher`s exist).

    Like actuators, sensors may be defined with a number of "attempt" methods. These methods are decorated with the `@attempt` decorator. The decorator ensures that the action is prepared for execution after the agent has decided upon it. Since sensing happens __before__ the call to `__cycle__` (see `Agent` class documentation for details), decisions to actively sense are made on the previous cycle.

    A typical example might look as follows:
    ```
    class MyAgent(Agent):
        def __cycle__(self):
            self.my_sensor.move(self.direction)


    class MySensor(Sensor):
        @attempt()
        def get_position(self):
            # this action is defined according to the environments state API.
            return GetPositionAction()
    ```

    An attempt method will always return the action that the agent wishes to take. It is possible to directly pass an action to an attempt method, in which case the method might simply return it:
    ```
    @attempt()
    def sense(self, action: Action):
        return action
    ```
    More often, there will be some additional steps inside the attempt method which prepares the action for execution. This simplifies the logic present inside the agents `__cycle__` method and can allow for some more generic setups where the agent is unaware of the implementation details of an action.

    Sensors can also attached to agents that subclass `AgentRouted`, which will allow for automatic routing of received observations to methods defined in the agent that are decorated with `@observe`. As with actuators, the same kind of action routing can be done (see `Actuator` class documentation for details).
    """

    def __query__(self, state: State) -> None:
        """Method that will execute all current actions in the given environment `state`.

        Args:
            state (State): to execute actions in.

        Raises:
            TypeError: if `__sense__` does not return the correct type.
        """
        # get sense actions
        actions = self.__sense__()
        if not isinstance(actions, list | tuple):
            raise TypeError(
                f"`__sense__` must return a `tuple` of actions, received: {actions}"
            )
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
        """Called by a `Publisher` with events that the sensor has subscribed to receive.

        Args:
            message (Event): the event that sensor has subscribed to receive.
        """
        self._observations.push_all(self.__transduce__([message]))

    def __subscribe__(self) -> list[Subscribe]:
        """Subscription actions for this `Sensor`, these actions will be taken on the first call to `__query__`. During the lifetime of this `Sensor` subscription actions can be taken in the usual way as with any other action.

        Returns:
            List[Subscribe]: list of `Subscribe` actions to take.

        Example:
            TODO
        """
        return []

    def on_add(self, agent: Agent) -> None:  # noqa: D102
        super().on_add(agent)
        # call __subscribe__ to take initial subscription actions (if there are any)
        self._actions.extend(self.__subscribe__())
        Sensor.set_subscriber(self, self._actions)

    def __sense__(self) -> list[Event]:
        """This method can be overridden to create a `Sensor` that does not depend on calls to `attempt` methods. This is useful if the `Sensor` should always sense the same kind of data.

        __Example__:
        ```
        class MySensor(Sensor):
            def __sense__(self):
                # new actions should always be created, do not re-use events!
                return [GetPositionAction()]
        ```

        See Also:
            [`Actuator.__attempt__`]
        """
        return []

    @staticmethod
    def set_subscriber(sensor: Sensor, actions: list[Subscribe | Unsubscribe]):
        """Sets the subscriber to the given sensor sensor if it is None for each action in actions.

        Args:
            sensor (Sensor): sensor to use as the subscriber.
            actions (List[Subscribe  |  Unsubscribe]): action for which to set `subscriber` attribute.
        """
        for action in actions:
            if action.subscriber is None:
                # TODO this will currently call __notify__ of the agent... not this sensor!
                # it only works locally at the moment
                action.subscriber = sensor
