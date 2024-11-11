"""Module defining the class `Component`, see class documentation for details."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ...event import Observation, Action
from .._wrapper_observations import _Observations
from ...utils import int64_uuid

if TYPE_CHECKING:
    from ..agent import Agent
    from ...environment import State

__all__ = ("Component",)


class Component(ABC):
    """Base class for components that may be attached to an agent. These include: `Sensor` and `Actuator`, which are used by the agent for sensing the environment and performing actions to change its state."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)
        self._id: int = int64_uuid()
        # this will be set by the agent when this component is added to it.
        # generally it should not be accessed directly unless you know what you are doing!
        self._agent = None
        # actions to attempt in the current cycle to produce observations
        self._actions: list[Action] = []  # TODO allow async access here?
        # observations that result from taking action
        self._observations: _Observations = _Observations.empty()

    def on_add(self, agent: Agent) -> None:
        """Callback for when this `Component` is added to an `Agent`.

        Args:
            agent (Agent): agent that this `Component` was added to.
        """
        self._agent = agent

    def on_remove(self, agent: Agent) -> None:
        """Callback for when this `Component` is removed from an `Agent`.

        Args:
            agent (Agent): agent that this `Component` was removed from to.
        """
        self._agent = None

    @property
    def id(self):
        """Unique identifier for this [`Component`].

        Returns:
            [str]: unique identifier
        """
        return self._id

    def iter_observations(self):
        """Iterate over and consumes the observations that are currently stored in this `Component`.

        Yields:
            [Observation]: the most recent observation.
        """
        yield from filter(None, self._observations)

    def iter_actions(self):
        """Iterates (and consumes?TODO) the actions that are currently stored in this `Component`.

        Yields:
            [Action]: the most recent action.
        """
        yield from filter(None, self._actions)

    async def aiter_observations(self):
        """Not implemented."""
        raise NotImplementedError("TODO")

    async def aiter_actions(self):
        """Not implemented."""
        raise NotImplementedError("TODO")

    def __transduce__(self, events: list[Observation]) -> list[Observation]:
        """Convert a list of events to another list of events. This is typically used to implement a transformation of "raw" observations that this component may receive. There is no restiction on how this transformation is done, some events may even be removed or added.

        This should not be called manually, and is instead part of the agent's (or component's) cycle.

        Args:
            events (list[Observation]): events to transform

        Returns:
            list[Observation]: the transformed list of events
        """
        return events

    @abstractmethod
    def __query__(self, state: State) -> None:
        """Query the state of the environment (take an action).

        This should not be called manually, and is instead part of the agent's (or component's) cycle.

        Args:
            state (State): state of the environment.
        """

    def __str__(self):  # noqa: D105
        return f"{self.__class__.__name__}({self._id})"

    def __repr__(self):  # noqa: D105
        # TODO perhaps include information about the agent this component is attached to ?
        return str(self)

    @staticmethod
    def set_action_source(component: Component, actions: list[Action]):
        """Set the `source` attribute of each action in `actions` to be the `id` of this `Component`. Typically `component` is the component that is taking the actions.

        Args:
            component (Component): that is taking the actions
            actions (list[Action]): whoses sources should be set
        """
        for action in actions:
            # if action.source is None:
            # TODO this should be forced...?
            action.source = (component.id << 64) | component._agent.id

    @staticmethod
    def unpack_source(action: Action):
        """Unpack the source of an action into the component id and agent id.

        Args:
            action (Action): action with source to unpack

        Returns:
            tuple[int, int]: (component id, agent id)
        """
        component_id = action.source >> 64
        agent_id = action.source & 0xFFFFFFFFFFFFFFFF
        return component_id, agent_id
