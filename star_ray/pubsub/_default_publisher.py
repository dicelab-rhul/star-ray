from typing import Dict, Set, Type
from collections import defaultdict
from copy import deepcopy

from ._pubsub import Subscriber
from ._pubsub import Publisher
from ._action import _fully_qualified_name
from ..event import Event


class TopicPublisher(Publisher):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribers: Dict[str, Set[Subscriber]] = defaultdict(set)

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].add(subscriber)

    def unsubscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].discard(subscriber)


class EventPublisher(TopicPublisher):

    def subscribe(
        self,
        topic: str | Type[Event],
        subscriber: Subscriber,
    ) -> None:
        if not isinstance(topic, str):
            topic = _fully_qualified_name(topic)
        super().subscribe(topic, subscriber)

    def unsubscribe(self, topic: str | Type[Event], subscriber: Subscriber) -> None:
        if not isinstance(topic, str):
            topic = _fully_qualified_name(topic)
        super().unsubscribe(topic, subscriber)

    def notify_subscribers(self, message: Event) -> None:
        topic = _fully_qualified_name(type(message))
        for sub in self._subscribers[topic]:
            sub.__notify__(deepcopy(message))
        for sub in self._subscribers["*"]:
            sub.__notify__(deepcopy(message))

    @staticmethod
    def fully_qualified_name(event_type: Type[Event]):
        return _fully_qualified_name(event_type)
