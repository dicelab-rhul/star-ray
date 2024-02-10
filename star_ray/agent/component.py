import uuid
from abc import ABCMeta
from typing import List
from functools import wraps

import ray

from ..event import Event


class Component(metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self._id = str(uuid.uuid4())
        self._object_refs = []
        self._queries = []

    @property
    def id(self):
        return self._id

    def __query__(self, ambient):
        if isinstance(ambient, ray.actor.ActorHandle):
            self._object_refs = [
                ambient.__query__.remote(query) for query in self._queries
            ]
        else:
            self._object_refs = [ambient.__query__(query) for query in self._queries]
        # clear queries ready for the next cycle
        self._queries.clear()

    def get(self):
        if len(self._object_refs) > 0:
            if not isinstance(self._object_refs[0], ray.ObjectRef):
                return self._object_refs
            else:
                self._object_refs = [ray.get(obj_ref) for obj_ref in self._object_refs]
                return self._object_refs
        else:
            return []

    @staticmethod
    def action(fun):
        @wraps(fun)
        def wrapper(self, *args, **kwargs):
            action = fun(self, *args, **kwargs)
            self._queries.append(action)
            return action

        return wrapper


class Sensor(Component):
    def __query__(self, ambient):
        self._queries = self.__sense__()
        super().__query__(ambient)

    def __sense__(self, *args, **kwargs) -> List[Event]:
        return self._queries

    @staticmethod
    def action(fun):
        return Component.action(fun)


class Actuator(Component):
    def __query__(self, ambient):
        self._queries = self.__attempt__()
        super().__query__(ambient)

    def __attempt__(self, *args, **kwargs) -> List[Event]:
        return self._queries

    @staticmethod
    def action(fun):
        return Component.action(fun)
