"""Module defining the `Actuator` class. See class documentation for details."""

from __future__ import annotations
from typing import TYPE_CHECKING

from .component import Component

if TYPE_CHECKING:
    from ...environment import State

__all__ = ("Actuator",)


class Actuator(Component):
    """Base class for an actuator. `Actuator`s may be attached to an `Agent` and will allow them to take actions to mutate the environment state. They run as part of `__execute__` in the agents cycle.

    Like sensors, actuators are typically defined with a number of "attempt" methods. These methods are decorated with the `@attempt` decorator. The decorator ensures that the action is prepared for execution after the agent has decided upon it.

    A typical example might look as follows:
    ```
    class MyAgent(Agent):
        def __cycle__(self):
            self.my_actuator.move(self.direction)


    class MyActuator(Actuator):
        @attempt()
        def move(self, direction: float):
            return MoveAction(direction)
    ```

    An attempt method will always return the action that the agent wishes to take. It is possible to directly pass an action to an attempt method, in which case the method might simply return it:
    ```
    @attempt()
    def take(self, action: Action):
        return action
    ```
    More often, there will be some additional steps inside the attempt method which prepares the action for execution. This simplifies the logic present inside the agents `__cycle__` method and can allow for some more generic setups where the agent is unaware of the implementation details of an action.

    In some situations we may want an actuator to always take some action (or set of actions) regardless of the agents decision. In this case we can override the `__attempt__` method, see method documentation for details.

    Actuators can also attached to agents that subclass `AgentRouted`, which will allow for automatic routing of decisions to their respective actuators (we don't need to call attempt methods explicitly) see this class for details.
    """

    def __query__(self, state: State) -> None:
        """Method that will execute all current actions in the given environment `state`.

        Args:
            state (State): to execute actions in.

        Raises:
            TypeError: if `__attempt__` does not return the correct type.
        """
        # get actions
        actions = self.__attempt__()
        if not isinstance(actions, list | tuple):
            raise TypeError(
                f"`__attempt__` must return a `tuple` of actions, received: {actions}"
            )
        self._actions.extend(actions)
        self._actions = list(filter(None, self._actions))
        # set the source of these actions to this actuator
        Component.set_action_source(self, self._actions)
        # attempt the sense act and get the resulting observations
        observations = state.__update__(self._actions)
        # preprocess the observations ready to be received by the agent
        self._observations.push_all(self.__transduce__(observations))
        # clear sense actions ready for the next execution cycle
        self._actions.clear()

    def __attempt__(self):
        """This method can be overriden to create an actuator that does not depend on calls to `attempt` methods. This is useful if the actuator should always perform the same kind of action independently of the agents decision making.

        The default implementation of this method simply returns any actions returned by an `attempt` methods.

        Example:
        ```
        class FowardActuator(Actuator):
            def __attempt__(self):
                # new actions should always be created, do not re-use events!
                return [QueryMoveForward()]
        ```
        See also:
            [`Sensor.__sense__`]
        """
        return []
