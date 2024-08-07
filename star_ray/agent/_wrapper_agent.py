"""Internal base classes that manage local/remote/async agents in an `Ambient`. They make use of the `_Future` API to streamline method/property access."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod
import asyncio
import ray
from ray.actor import ActorHandle

from ..utils import _Future
from .agent import Agent

if TYPE_CHECKING:
    from ..environment import State

__all__ = ("_Agent",)


class _Agent(ABC):
    """Internal base class for streamlining method/property access on agents for local/remote/async agents."""

    def __init__(self, agent: Any):
        super().__init__()
        self._inner = agent

    @staticmethod
    def is_agent_async(agent: Any):
        """Does the agent define asynchronous methods? (declared `async`)."""
        return (
            asyncio.iscoroutinefunction(agent.__sense__)
            and asyncio.iscoroutinefunction(agent.__execute__)
            and asyncio.iscoroutinefunction(agent.__cycle__)
        )

    @staticmethod
    def is_agent_sync(agent: Any):
        """Does the agent define synchronous methods? (not declared `async`)."""
        return not (
            asyncio.iscoroutinefunction(agent.__sense__)
            or asyncio.iscoroutinefunction(agent.__execute__)
            or asyncio.iscoroutinefunction(agent.__cycle__)
        )

    @staticmethod
    def is_agent_remote(agent: Any):
        """Is the agent a remote ray actor?"""
        return isinstance(agent, ActorHandle)

    @staticmethod
    def new(agent: Any):
        """Factory function that will wrap the given agent in one of three wrappers: `_AgentWrapperRemote`, `_AgentWrapperLocal`, `_AgentWrapperAsync` depending on its type and whether its method definitions are `async`.

        Args:
            agent (Any): the agent (or remote handle) to wrap.

        Raises:
            TypeError: If the agent does not meet the type requirements.

        Returns:
            _Agent: the wrapped agent.
        """
        if isinstance(agent, _Agent):
            return agent
        elif _Agent.is_agent_remote(agent):
            return _AgentWrapperRemote(agent)
        elif isinstance(agent, Agent):
            # the agent is local, is it sync or async?
            if _Agent.is_agent_async(agent):
                return _AgentWrapperLocalAsync(agent)
            elif _Agent.is_agent_sync(agent):
                return _AgentWrapperLocal(agent)
            else:
                raise TypeError(
                    f"Invalid method definitions in agent {agent}, __cycle__, __sense__, __execute__ must be declared all async or all sync."
                )
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
    def __terminate__(self, state: State) -> _Future:
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

    def __terminate__(self, state: State) -> _Future:
        return _Future.call_remote(self._inner.__terminate__, state)
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

    def __terminate__(self, state: State) -> _Future:
        return _Future.call_sync(self._inner.__terminate__, state)

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

    def __terminate__(self, state: State) -> _Future:
        return _Future.call_async(self._inner.__terminate__, state)
