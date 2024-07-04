from typing import List, Any
from abc import ABC, abstractmethod
from collections import deque
import ray

from ..event import Event


class _Observations(ABC):

    @staticmethod
    def new(objects: List[Event | ray.ObjectRef]):
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

    @abstractmethod
    def __next__(self) -> Event:
        pass


class _ObservationsRemote(_Observations):

    def __init__(self, objects):
        super().__init__()
        self._objects = deque(objects)

    def __len__(self):
        return self._objects.count

    def is_empty(self):
        return self._objects.count == 0

    def push(self, item: ray.ObjectRef) -> None:
        self._objects.append(item)

    def push_all(self, items: List[ray.ObjectRef]) -> None:
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

    def __init__(self, objects):
        super().__init__()
        self._objects = deque(objects)

    def __len__(self):
        return self._objects.count

    def is_empty(self):
        return self._objects.count == 0

    def push_all(self, items: List[Event]) -> None:
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
