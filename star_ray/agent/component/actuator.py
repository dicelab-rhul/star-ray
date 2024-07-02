""" Defines 'active' component classes : [Component], [Actuator], [Sensor]. An active component is one that makes requests to the environment (actions) to sense (in the case of sensors) and to act (in the case of actuators). Sensing and acting are tied to the agents event cycle which is typically managed by the environment execution scheduler. See also 'passive' components TODO link. """

from __future__ import annotations  # make type hints work :)
from typing import TYPE_CHECKING

from .component import Component

if TYPE_CHECKING:
    from ...environment.wrapper_state import State


class Actuator(Component):

    def __query__(self, state: State):
        # get actions
        self._actions = self.__attempt__()
        # set the source of these actions to this actuator
        self._set_source(self._actions)
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
        return self._actions
