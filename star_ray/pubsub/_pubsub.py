from weakref import ref
from abc import ABC, abstractmethod
from typing import Any
from ray.actor import ActorHandle

__all__ = ("Subscriber", "Publisher")


class Subscriber(ABC):

    @abstractmethod
    def __notify__(self, message: Any) -> None:
        pass


def _SubscriberWrapper(subscriber: Any):
    if isinstance(subscriber, Subscriber):
        return _SubscriberLocal(subscriber)
    elif isinstance(subscriber, ActorHandle):
        return _SubscriberRemote(subscriber)
    else:
        raise TypeError(
            f"subscriber must of type {Subscriber} or be a remote ray actor."
        )


class _SubscriberLocal(Subscriber):

    def __init__(self, subscriber: Subscriber):
        self._handle = ref(subscriber)

    def __notify__(self, message: Any) -> bool:
        sub = self._handle()
        if sub:
            sub.__notify__(message)
        else:
            raise ValueError("Subscriber was garbage collected before unsubscribing.")

    def __eq__(self, other):
        if isinstance(other, _SubscriberRemote):
            return self._handle == other._handle
        return False

    def __hash__(self):
        return hash(self._handle)

    def __repr__(self) -> str:
        return f"Subscriber@local({repr(self._handle())})"

    def __str__(self):
        return repr(self)


class _SubscriberRemote(Subscriber):

    def __init__(self, actor_handle: ActorHandle):
        self._handle = actor_handle

    def __notify__(self, message: Any) -> None:
        self._handle.__notify__.remote(message)

    def __eq__(self, other):
        if isinstance(other, _SubscriberRemote):
            return self._handle == other._handle
        return False

    def __hash__(self):
        return hash(self._handle)

    def __repr__(self) -> str:
        return f"Subscriber@remote({repr(self._handle)})"

    def __str__(self):
        return str(self._handle)


class Publisher(ABC):

    @abstractmethod
    def subscribe(self, topic: Any, subscriber: Subscriber) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, topic: Any, subscriber: Subscriber) -> None:
        pass

    @abstractmethod
    def notify_subscribers(self, message: Any) -> None:
        pass
