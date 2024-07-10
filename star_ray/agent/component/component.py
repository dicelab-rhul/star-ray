from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import List, Any, TYPE_CHECKING
from functools import wraps

from ...event import Observation, Action
from ..wrapper_observations import _Observations
from ...utils import int64_uuid

if TYPE_CHECKING:
    from ..agent import Agent
    from ...environment import State


__all__ = (
    "ComponentMeta",
    "Component",
    "attempt",
)

# ATTEMPT_METHOD_CLS_VAR = "__attemptmethods__"
# IS_ATTEMPT_VAR = "is_attempt"


# def _is_attempt_method(obj):
#     return callable(obj) and hasattr(obj, IS_ATTEMPT_VAR)
#     # return inspect.ismethod(obj) and hasattr(obj, IS_ATTEMPT_VAR)


# TODO fix attempt methods, use a _TypeRouter
class _ComponentMeta(type):
    def __new__(cls, name, bases, dct):
        # TODO AgentRouted is now a thing, we dont use this meta class any more
        # Get all methods decorated with the attempt_decorator
        # attempt_methods = [attr for _,
        #                    attr in dct.items() if _is_attempt_method(attr)]
        # # get attempt methods in base classes, these should not change...
        # for base in bases:
        #     attempt_methods.extend(getattr(base, ATTEMPT_METHOD_CLS_VAR, []))
        # dct[ATTEMPT_METHOD_CLS_VAR] = attempt_methods
        return super().__new__(cls, name, bases, dct)


class ComponentMeta(ABCMeta, _ComponentMeta):
    pass


class Component(metaclass=ComponentMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id: int = int64_uuid()
        # this will be set by the agent when this component is added to it.
        # generally it should not be accessed directly unless you know what you are doing!
        self._agent = None
        # actions to attempt in the current cycle to produce observations
        self._actions: List[Action] = []  # TODO allow async access here?
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
        raise NotImplementedError("TODO")

    async def aiter_actions(self):
        raise NotImplementedError("TODO")

    def __transduce__(self, events: List[Observation]) -> List[Observation]:
        return events

    @abstractmethod
    def __query__(self, state: State) -> None:
        """Query the state of the environment (take an action). This should not be called manually and is instead called as part of the agents cycle.

        Args:
            state (State): state of the environment.
        """

    def __str__(self):
        return f"{self.__class__.__name__}({self._id})"

    def __repr__(self):
        # TODO perhaps include information about the agent this component is attached to ?
        return str(self)

    @staticmethod
    def set_action_source(component: Component, actions: List[Action]):
        for action in actions:
            if action.source is None:
                action.source = component.id
