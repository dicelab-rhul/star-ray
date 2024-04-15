from collections import defaultdict
from copy import deepcopy
from typing import Dict, Set

from ..event import Event
from ._pubsub import Subscriber
from ._pubsub import Publisher
from ._action import _fully_qualified_name


class TypeTopicPublisher(Publisher):

    def __init__(self):
        super().__init__()
        self._subscribers: Dict[str, Set[Subscriber]] = defaultdict(set)

    def subscribe(self, topic: type | str, subscriber: Subscriber) -> None:
        if isinstance(topic, type):
            topic = _fully_qualified_name(topic)
        assert isinstance(topic, str)
        self._subscribers[topic].add(subscriber)

    def unsubscribe(self, topic: type | str, subscriber: Subscriber) -> None:
        if isinstance(topic, type):
            topic = _fully_qualified_name(topic)
        assert isinstance(topic, str)
        self._subscribers[topic].discard(subscriber)

    def notify_subscribers(self, message: Event) -> None:
        topic = _fully_qualified_name(type(message))
        for sub in self._subscribers[topic]:
            sub.__notify__(deepcopy(message))
