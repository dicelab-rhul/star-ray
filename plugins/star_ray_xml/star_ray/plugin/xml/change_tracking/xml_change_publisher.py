from typing import Any, Type, Dict, Set
from collections import defaultdict
from copy import deepcopy

from star_ray.environment import Ambient
from star_ray.event import (
    Action,
    Observation,
    ActiveObservation,
    ErrorActiveObservation,
)
from star_ray.pubsub import Publisher
from star_ray.pubsub import Subscribe, Unsubscribe, Subscriber

from .xml_change_tracking import has_change_tracking


class XMLElementChangeObservation(Observation):
    element_id: str


class XMLChangeObservation(Observation):
    xpath: str


class _SubscribeXMLChangeBase:
    pass


class SubscribeXMLChange(Subscribe, _SubscribeXMLChangeBase):
    pass


class UnsubscribeXMLChange(Unsubscribe, _SubscribeXMLChangeBase):
    pass


class SubscribeXMLElementChange(Subscribe, _SubscribeXMLChangeBase):
    pass


class UnsubscribeXMLElementChange(Unsubscribe, _SubscribeXMLChangeBase):
    pass


class _XMLChangePublisherBase(Publisher):
    def __init__(self):
        super().__init__()
        self._subscribers: Dict[str, Set[Subscriber]] = defaultdict(set)

    def subscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].add(subscriber)

    def unsubscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].discard(subscriber)


class XMLElementChangePublisher(_XMLChangePublisherBase):

    def notify_subscribers(self, message: Dict[str, Any]) -> None:
        element_id = message["element_id"]  # this is defined in xml_tracking_element.py
        if element_id is None:
            return
        for sub in self._subscribers[element_id]:
            event = XMLElementChangeObservation(
                element_id=element_id, values=deepcopy(message["attributes"])
            )
            sub.__notify__(event)


class XMLChangePublisher(_XMLChangePublisherBase):

    def notify_subscribers(self, message: Dict[str, Any]) -> None:
        xpath = message["xpath"]  # this is defined in xml_tracking_element.py
        for sub in self._subscribers[xpath]:
            event = XMLChangeObservation(
                xpath=xpath, values=deepcopy(message["attributes"])
            )
            sub.__notify__(event)
        # notify all wildcard subscribers
        # TODO remove duplicates, this might end up being expensive for something that doesnt happen often
        for sub in self._subscribers["*"]:
            event = XMLChangeObservation(
                xpath=xpath, values=deepcopy(message["attributes"])
            )
            sub.__notify__(event)


def xml_change_publisher(cls: Type[Ambient]):
    # NOTE: this publisher will only publish changes to elements that have a unique "id"
    # subscribers should use this id as the subscription topic. TODO document this further.

    # TODO cls must be an ambient
    if not has_change_tracking(cls):
        raise TypeError(
            "`xml_change_publisher` requires change tracking, make use of the `@change_tracking` decorator to fix this error."
        )

    class XMLChangeAmbient(cls):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._xml_change_publisher = XMLChangePublisher()
            self._xml_element_change_publisher = XMLElementChangePublisher()
            self.add_xml_change_callback(self.__notify_xml_change__)

        def __select__(self, action: Action):
            if not isinstance(action, _SubscribeXMLChangeBase):
                return super().__select__(action)
            else:
                try:
                    return self.__xml_change_subscription__(action)
                except Exception as e:
                    return ErrorActiveObservation(exception=e, action_id=action)

        def __notify_xml_change__(self, message):
            self._xml_change_publisher.notify_subscribers(message)
            self._xml_element_change_publisher.notify_subscribers(message)

        def __xml_change_subscription__(self, action: _SubscribeXMLChangeBase):
            if isinstance(action, SubscribeXMLChange):
                self._xml_change_publisher.subscribe(action.topic, action.subscriber)
            elif isinstance(action, UnsubscribeXMLChange):
                self._xml_change_publisher.unsubscribe(action.topic, action.subscriber)
            elif isinstance(action, SubscribeXMLElementChange):
                self._xml_element_change_publisher.subscribe(
                    action.topic, action.subscriber
                )
            elif isinstance(action, UnsubscribeXMLElementChange):
                self._xml_element_change_publisher.unsubscribe(
                    action.topic, action.subscriber
                )
            else:
                raise TypeError(f"Unknown xml change subscription type: {type(action)}")
            return ActiveObservation(action_id=action)

    return XMLChangeAmbient
