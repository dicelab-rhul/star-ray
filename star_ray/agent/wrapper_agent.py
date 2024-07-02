from __future__ import annotations  # make type hints work :)
from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod
import asyncio
import ray
from ray.actor import ActorHandle

from ..utils import _Future
from .agent import Agent

if TYPE_CHECKING:
    from ..environment.wrapper_state import State

__all__ = ("_Agent",)


class _Agent(ABC):
    """TODO"""

    def __init__(self, agent: Any):
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
    def __initialise__(self, state: State) -> _Future:
        pass

    @abstractmethod
    def __sense__(self, state: State) -> _Future:
        pass

    @abstractmethod
    def __cycle__(self) -> _Future:
        pass

    @abstractmethod
    def __execute__(self, state: State) -> _Future:
        pass

    @abstractmethod
    def __terminate__(self) -> _Future:
        pass

    @abstractmethod
    def get_id(self) -> Any:
        pass

    @abstractmethod
    def get_inner(self) -> Any:
        pass

    @property
    @abstractmethod
    def is_alive(self) -> bool:
        pass

    @property
    @abstractmethod
    def id(self) -> Any:
        pass


class _AgentWrapperRemote(_Agent):

    def __initialise__(self, state: State) -> _Future:
        return _Future.call_remote(self._inner.__initialise__, state)

    def __sense__(self, state: State) -> _Future:
        return _Future.call_remote(self._inner.__sense__, state)

    def __cycle__(self) -> _Future:
        return _Future.call_remote(self._inner.__cycle__)

    def __execute__(self, state: State) -> _Future:
        return _Future.call_remote(self._inner.__execute__, state)

    def __terminate__(self) -> _Future:
        return _Future.call_remote(self._inner.__terminate__)
        # TODO?
        # ray.kill(self._inner, no_restart=True)

    def get_inner(self):
        return self._inner

    def get_id(self):
        return self.id

    @property
    def is_alive(self) -> bool:
        return ray.get(self._inner.get_is_alive.remote())

    @property
    def id(self) -> Any:
        return ray.get(self._inner.get_id.remote())


class _AgentWrapperLocal(_Agent):

    def __initialise__(self, state: State) -> _Future:
        return _Future.call_sync(self._inner.__initialise__, state)

    def __sense__(self, state: State) -> _Future:
        return _Future.call_sync(self._inner.__sense__, state)

    def __cycle__(self) -> _Future:
        return _Future.call_sync(self._inner.__cycle__)

    def __execute__(self, state: State) -> _Future:
        return _Future.call_sync(self._inner.__execute__, state)

    def __terminate__(self):
        return _Future.call_sync(self._inner.__terminate__)

    def get_inner(self):
        return self._inner

    def get_id(self):
        return self._inner.id

    @property
    def is_alive(self) -> bool:
        return self._inner.is_alive

    @property
    def id(self) -> Any:
        return self._inner.id


class _AgentWrapperLocalAsync(_AgentWrapperLocal):

    def __initialise__(self, state: State) -> _Future:
        return _Future.call_async(self._inner.__initialise__, state)

    def __sense__(self, state: State) -> _Future:
        return _Future.call_async(self._inner.__sense__, state)

    def __cycle__(self) -> _Future:
        return _Future.call_async(self._inner.__cycle__)

    def __execute__(self, state: State) -> _Future:
        return _Future.call_async(self._inner.__execute__, state)

    def __terminate__(self):
        return _Future.call_async(self._inner.__terminate__)
