from pydantic import validator
from typing import Type
import ray

from ..event import Action
from ._pubsub import Subscriber, _SubscriberLocal, _SubscriberRemote

__all__ = ("Subscribe", "Unsubscribe")


class _SubscriptionActionBase(Action):

    topic: str
    subscriber: Subscriber

    @validator("subscriber", pre=True, always=True)
    @classmethod
    def _validate_subscriber(cls, subscriber: Subscriber):
        if ray.is_initialized():
            ctx = ray.get_runtime_context()
            if ctx.worker.mode:
                return _SubscriberRemote(ctx.current_actor)
        return _SubscriberLocal(subscriber)  # uses a weak reference

    @validator("topic", pre=True, always=True)
    @classmethod
    def _validate_topic(cls, topic: str | Type):
        if isinstance(topic, str):
            return topic
        elif isinstance(topic, type):
            return _fully_qualified_name(topic)
        else:
            raise TypeError(f"Invalid topic: {topic} must be a string or type.")

    class Config:
        arbitrary_types_allowed = True


class Subscribe(_SubscriptionActionBase):
    pass


class Unsubscribe(_SubscriptionActionBase):
    pass


def _fully_qualified_name(cls):
    return cls.__module__ + "." + cls.__qualname__
