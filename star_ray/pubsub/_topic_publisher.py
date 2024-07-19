from collections import defaultdict

from ._pubsub import Subscriber
from ._pubsub import Publisher


class TopicPublisher(Publisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribers: dict[str, set[Subscriber]] = defaultdict(set)

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].add(subscriber)

    def unsubscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].discard(subscriber)
