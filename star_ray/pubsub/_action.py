from typing import Any

from pydantic import field_validator, Field
import ray

from ..event import Action
from ._pubsub import Subscriber, _SubscriberLocal, _SubscriberRemote

__all__ = ("Subscribe", "Unsubscribe")


class _SubscriptionActionBase(Action):
    topic: Any
    subscriber: Subscriber | None = Field(default_factory=lambda: None)

    @field_validator("subscriber", mode="before")
    @classmethod
    def _validate_subscriber(cls, subscriber: Subscriber | None):
        if subscriber is None:
            return None
        if ray.is_initialized():
            ctx = ray.get_runtime_context()
            if ctx.worker.mode:
                return _SubscriberRemote(ctx.current_actor)
        return _SubscriberLocal(subscriber)  # uses a weak reference

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True


class Subscribe(_SubscriptionActionBase):
    pass


class Unsubscribe(_SubscriptionActionBase):
    pass
