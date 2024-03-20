from __future__ import annotations
from typing import Union, List, TYPE_CHECKING
from abc import ABC, abstractmethod

import ray
from ray.actor import ActorHandle
from ..event import Event
from .ambient import Ambient

from ..agent.wrapper_observations import (
    _ObservationsLocal,
    _ObservationsRemote,
    _Observations,
)

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
    def update(self, actions: List[Event]) -> _Observations:
        pass

    @abstractmethod
    def select(self, actions: List[Event]) -> _Observations:
        pass

    @abstractmethod
    def get_agents(self) -> List[_Agent]:
        pass


class _StateWrapperRemote(_State):
    def __init__(self, ambient: ActorHandle):
        self._inner = ambient

    def update(self, actions: List[Event]) -> _Observations:
        return _ObservationsRemote(
            [self._inner.__update__.remote(query) for query in actions]
        )

    def select(self, actions: List[Event]) -> _Observations:
        return _ObservationsRemote(
            [self._inner.__select__.remote(query) for query in actions]
        )

    def get_agents(self) -> List[_Agent]:
        return ray.get(self._inner.get_agents.remote())


class _StateWrapper(_State):

    def __init__(self, ambient: Ambient):
        self._inner = ambient

    def update(self, actions: List[Event]) -> _Observations:
        return _ObservationsLocal([self._inner.__update__(query) for query in actions])

    def select(self, actions: List[Event]) -> _Observations:
        return _ObservationsLocal([self._inner.__select__(query) for query in actions])

    def get_agents(self) -> List[_Agent]:
        return self._inner.get_agents()
