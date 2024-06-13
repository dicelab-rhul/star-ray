from typing import Union, List, Any
from abc import ABC, abstractmethod
import ray
from ray import ObjectRef
import asyncio

from ..event import Event

from collections import deque


class _Observations(ABC):

    @staticmethod
    def new(objects):
        if len(objects) == 0:
            return _Observations.empty()
        elif isinstance(objects[0], ObjectRef):
            return _ObservationsRemote(objects)
        elif isinstance(objects[0], Event):
            return _ObservationsLocal(objects)
        else:
            raise TypeError(f"Invalid observation type {type(objects[0])}.")

    @staticmethod
    def empty():
        return _ObservationsLocal([])

    @abstractmethod
    def push_all(self, items: List[Any]) -> None:
        pass

    @abstractmethod
    def push(self, item: Any) -> None:
        pass

    @abstractmethod
    def pop(self) -> Event:
        pass

    @abstractmethod
    def __iter__(self):
        pass

    # @abstractmethod
    # async def __aiter__(self):
    #     pass


class _ObservationsRemote(_Observations):

    def __init__(self, objects):
        super().__init__()
        self._objects = deque(objects)

    def push(self, item: ObjectRef) -> None:
        self._objects.append(item)

    def push_all(self, items: List[Any]) -> None:
        self._objects.extend(items)

    def pop(self) -> Event:
        return ray.get(self._objects.popleft())

    def __iter__(self):
        return self

    def __next__(self):
        if not self._objects:
            raise StopIteration
        return ray.get(self._objects.popleft())

    # async def __aiter__(self):
    #     return self

    # async def __anext__(self):
    #     if not self._objects:
    #         raise StopAsyncIteration
    #     object_ref: ObjectRef = self._objects.popleft()
    #     event = await object_ref
    #     return event


class _ObservationsLocal(_Observations):

    def __init__(self, objects):
        super().__init__()
        self._objects = deque(objects)

    def push_all(self, items: List[Any]) -> None:
        self._objects.extend(items)

    def push(self, item: ObjectRef) -> None:
        self._objects.append(item)

    def pop(self) -> Event:
        return self._objects.popleft()

    def __iter__(self):
        return self

    def __next__(self):
        if not self._objects:
            raise StopIteration
        return self._objects.popleft()
