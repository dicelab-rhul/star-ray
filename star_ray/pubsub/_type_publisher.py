from typing import Any
from functools import partial
from ._pubsub import Publisher, Subscriber
from ..utils import _LOGGER, TypeRouter


class TypePublisher(Publisher):
    def __init__(self, cache_size=1024):
        super().__init__()
        self._router = TypeRouter(cache_size=cache_size)
        self._subscribers = dict()

    def subscribe(
        self,
        topic: type | list[type],
        subscriber: Subscriber,
    ) -> None:
        _subscriber = partial(subscriber.__notify__)
        self._router.add(_subscriber, route_types=topic)
        _LOGGER.debug(f"{self} new subscription: {subscriber} to topic: {topic}")

    def unsubscribe(self, topic: Any, subscriber: Subscriber) -> None:
        raise NotImplementedError(
            "TODO - requires `remove` implementation in TypeRouter"
        )

    def publish(self, message: Any) -> None:
        self._router(message)
