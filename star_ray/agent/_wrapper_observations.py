"""Internal base classes that manage local/remote observations in `Component` implementations."""

from typing import Any
from abc import ABC, abstractmethod
from collections import deque
import ray

from ..event import Event


class _Observations(ABC):
    """Abstract base class for managing collections of observations, either remote or local. This class provides a common interface for operations on a collection of observations, which can be either local (`Event` objects) or remote (`ray.ObjectRef` objects).

    The class is used internally by `Component` classes to seemlessly manage the retreival of remote (or local) data.

    Important note: Iterating over the collection will consume it.
    """

    @staticmethod
    def new(objects: list[Event | ray.ObjectRef]):
        if len(objects) == 0:
            return _Observations.empty()
        elif isinstance(objects[0], ray.ObjectRef):
            return _ObservationsRemote(objects)
        elif isinstance(objects[0], Event):
            return _ObservationsLocal(objects)
        else:
            raise TypeError(f"Invalid observation type {type(objects[0])}.")

    @staticmethod
    def empty():
        return _ObservationsLocal([])

    @abstractmethod
    def is_empty(self):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def push_all(self, items: list[Any]) -> None:
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

    @abstractmethod
    def __next__(self) -> Event:
        pass


class _ObservationsRemote(_Observations):
    """Collection of remote observations."""

    def __init__(self, objects):
        super().__init__()
        self._objects = deque(objects)

    def __len__(self):
        return self._objects.count

    def is_empty(self):
        return self._objects.count == 0

    def push(self, item: ray.ObjectRef) -> None:
        self._objects.append(item)

    def push_all(self, items: list[ray.ObjectRef]) -> None:
        self._objects.extend(items)

    def pop(self) -> Event:
        return ray.get(self._objects.popleft())

    def __iter__(self):
        return self

    def __next__(self) -> Event:
        if not self._objects:
            raise StopIteration
        return ray.get(self._objects.popleft())


class _ObservationsLocal(_Observations):
    """Collection of local observations."""

    def __init__(self, objects):
        super().__init__()
        self._objects = deque(objects)

    def __len__(self):
        return self._objects.count

    def is_empty(self):
        return self._objects.count == 0

    def push_all(self, items: list[Event]) -> None:
        self._objects.extend(items)

    def push(self, item: Event) -> None:
        self._objects.append(item)

    def pop(self) -> Event:
        return self._objects.popleft()

    def __iter__(self):
        return self

    def __next__(self) -> Event:
        if not self._objects:
            raise StopIteration
        return self._objects.popleft()
