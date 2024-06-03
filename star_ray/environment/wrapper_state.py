from __future__ import annotations
from typing import Union, List, TYPE_CHECKING, Any
from abc import ABC, abstractmethod
import ray
from ray.actor import ActorHandle
from .ambient import Ambient

if TYPE_CHECKING:
    from ..agent.wrapper_agent import _Agent
    from ..pubsub import Subscribe, Unsubscribe
    from ..event import Event

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

    @property
    @abstractmethod
    def is_alive(self):
        pass

    @abstractmethod
    async def __initialise__(self):
        pass

    @abstractmethod
    def __subscribe__(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def __update__(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def __select__(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def get_agents(self) -> List[_Agent]:
        pass


class _StateWrapperRemote(_State):
    def __init__(self, ambient: ActorHandle):
        self._inner = ambient

    @property
    def is_alive(self):
        return self._inner.get_is_alive.remote()

    async def __initialise__(self):
        # initialise the remote ambient, wait for the call to complete so that we can be sure everything is ready.
        return await self._inner.__initialise__.remote()

    def __subscribe__(self, actions: List[Subscribe | Unsubscribe]) -> List[Any]:
        return [self._inner.__subscribe__.remote(query) for query in actions]

    def __update__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__update__.remote(query) for query in actions]

    def __select__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__select__.remote(query) for query in actions]

    def get_agents(self) -> List[_Agent]:
        return ray.get(self._inner.get_agents.remote())


class _StateWrapper(_State):

    def __init__(self, ambient: Ambient):
        self._inner = ambient

    @property
    def is_alive(self):
        return self._inner.get_is_alive()

    async def __initialise__(self):
        return await self._inner.__initialise__()

    def __subscribe__(self, actions: List[Subscribe | Unsubscribe]) -> List[Any]:
        return [self._inner.__subscribe__(query) for query in actions]

    def __update__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__update__(query) for query in actions]

    def __select__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__select__(query) for query in actions]

    def get_agents(self) -> List[_Agent]:
        return self._inner.get_agents()
