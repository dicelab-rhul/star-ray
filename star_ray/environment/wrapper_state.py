from __future__ import annotations
from typing import Union, List, TYPE_CHECKING, Any
from abc import ABC, abstractmethod
import asyncio
import ray
from ray.actor import ActorHandle
from ..event import Event
from .ambient import Ambient

if TYPE_CHECKING:
    from ..agent.wrapper_agent import _Agent

__all__ = ("_State",)


class _State(ABC):

    @staticmethod
    def new(ambient: Union[Ambient, ActorHandle]):
        if isinstance(ambient, ActorHandle):
            return _StateWrapperRemote(ambient)
        elif isinstance(ambient, Ambient):
            return _StateWrapper(ambient)
        else:
            raise TypeError(f"Invalid ambient type {type(ambient)}.")

    @abstractmethod
    async def initialise(self):
        pass

    @abstractmethod
    def update(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def select(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def get_agents(self) -> List[_Agent]:
        pass


class _StateWrapperRemote(_State):
    def __init__(self, ambient: ActorHandle):
        self._inner = ambient

    async def initialise(self):
        # initialise the remote ambient, wait for the call to complete so that we can be sure everything is ready.
        return await self._inner.initialise.remote()

    def update(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__update__.remote(query) for query in actions]

    def select(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__select__.remote(query) for query in actions]

    def get_agents(self) -> List[_Agent]:
        return ray.get(self._inner.get_agents.remote())


class _StateWrapper(_State):

    def __init__(self, ambient: Ambient):
        self._inner = ambient

    async def initialise(self):
        return await self._inner.initialise()

    def update(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__update__(query) for query in actions]

    def select(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__select__(query) for query in actions]

    def get_agents(self) -> List[_Agent]:
        return self._inner.get_agents()
