from __future__ import annotations  # make type hints work :)
from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod
import asyncio
import ray
from ray.actor import ActorHandle

from ..utils import _Future
from .agent import Agent

if TYPE_CHECKING:
    from ..environment.wrapper_state import _State

__all__ = ("_Agent",)


class _Agent(ABC):
    """TODO"""

    def __init__(self, agent):
        super().__init__()
        self._inner = agent

    @staticmethod
    def new(agent: Any):
        if isinstance(agent, _Agent):
            return agent
        elif isinstance(agent, ActorHandle):
            return _AgentWrapperRemote(agent)
        elif isinstance(agent, Agent):
            # TODO streamline this check somewhere...
            if (
                asyncio.iscoroutinefunction(agent.__sense__)
                and asyncio.iscoroutinefunction(agent.__execute__)
                and asyncio.iscoroutinefunction(agent.__cycle__)
            ):
                return _AgentWrapperLocalAsync(agent)
            elif not (
                asyncio.iscoroutinefunction(agent.__sense__)
                or asyncio.iscoroutinefunction(agent.__execute__)
                or asyncio.iscoroutinefunction(agent.__cycle__)
            ):
                return _AgentWrapperLocal(agent)
            else:
                raise TypeError(
                    f"Invalid method definitions in agent {agent}, __cycle__, __sense__, __execute__ must be declared all async or all sync."
                )
        else:
            raise TypeError(f"Invalid type for agent {type(agent)}.")

    @abstractmethod
    def sense(self, state: _State) -> _Future:
        pass

    @abstractmethod
    def cycle(self) -> _Future:
        pass

    @abstractmethod
    def execute(self, state: _State) -> _Future:
        pass

    @abstractmethod
    def kill(self) -> _Future:
        pass

    @abstractmethod
    def get_id(self):
        pass

    @abstractmethod
    def get_inner(self):
        pass

    @property
    @abstractmethod
    def id(self):
        pass


class _AgentWrapperRemote(_Agent):

    def sense(self, state: _State) -> _Future:
        return _Future.call_remote(self._inner.__sense__, state)

    def cycle(self) -> _Future:
        return _Future.call_remote(self._inner.__cycle__)

    def execute(self, state: _State) -> _Future:
        return _Future.call_remote(self._inner.__execute__, state)

    @property
    def id(self):
        return ray.get(self._inner.get_id.remote())

    def kill(self):
        return ray.kill(self._inner, no_restart=True)

    def get_inner(self):
        return self._inner

    def get_id(self):
        return self.id


class _AgentWrapperLocal(_Agent):

    def sense(self, state: _State) -> _Future:
        return _Future.call_sync(self._inner.__sense__, state)

    def cycle(self) -> _Future:
        return _Future.call_sync(self._inner.__cycle__)

    def execute(self, state: _State) -> _Future:
        return _Future.call_sync(self._inner.__execute__, state)

    @property
    def id(self):
        return self._inner.id

    def kill(self):
        pass

    def get_inner(self):
        return self._inner

    def get_id(self):
        return self.id


class _AgentWrapperLocalAsync(_AgentWrapperLocal):

    def sense(self, state: _State) -> _Future:
        return _Future.call_async(self._inner.__sense__, state)

    def cycle(self) -> _Future:
        return _Future.call_async(self._inner.__cycle__)

    def execute(self, state: _State) -> _Future:
        return _Future.call_async(self._inner.__execute__, state)
