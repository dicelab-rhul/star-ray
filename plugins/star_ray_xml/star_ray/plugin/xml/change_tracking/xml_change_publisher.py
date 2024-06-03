from typing import Any, Type, Dict, Set
from collections import defaultdict
from pydantic import validator
from copy import deepcopy
from ast import literal_eval

from star_ray.environment import Ambient
from star_ray.event import (
    Observation,
    ActiveObservation,
    ErrorActiveObservation,
)
from star_ray.pubsub import Publisher
from star_ray.pubsub import Subscribe, Unsubscribe, Subscriber

from .xml_change_tracking import has_change_tracking
from ..query_xpath import QueryXPath
from ..query_xml import QueryXML
from ..utils import _LOGGER


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
        _LOGGER.debug("%s subscribed to `%s` in publisher %s", subscriber, topic, self)

    def unsubscribe(self, topic: str, subscriber: Subscriber) -> None:
        self._subscribers[topic].discard(subscriber)
        _LOGGER.debug(
            "%s unsubscribed from `%s` in publisher %s", subscriber, topic, self
        )


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

    def __str__(self):
        return XMLElementChangePublisher.__name__


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

    def __str__(self):
        return XMLChangePublisher.__name__


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

        def __subscribe__(
            self, action: Subscribe | Unsubscribe
        ) -> ActiveObservation | ErrorActiveObservation:
            if isinstance(action, _SubscribeXMLChangeBase):
                try:
                    return self.__xml_change_subscription__(action)
                except Exception as e:
                    return ErrorActiveObservation(exception=e, action_id=action)
            else:
                return super().__subscribe__(action)

        def notify(self, event: Dict):
            self._xml_change_publisher.notify_subscribers(event)
            self._xml_element_change_publisher.notify_subscribers(event)
            super().notify(event)

        def __xml_change_subscription__(self, action: _SubscribeXMLChangeBase):
            if isinstance(action, SubscribeXMLChange):
                self._xml_change_publisher.subscribe(action.topic, action.subscriber)
                # it is often useful to get the state of the xpath
                response = self.__select__(
                    QueryXPath(xpath=action.topic, attributes=[])
                )
                response.action_id = action.id
                return response

            elif isinstance(action, UnsubscribeXMLChange):
                self._xml_change_publisher.unsubscribe(action.topic, action.subscriber)
            elif isinstance(action, SubscribeXMLElementChange):
                self._xml_element_change_publisher.subscribe(
                    action.topic, action.subscriber
                )
                # it is often useful to get the state of the element after subscribing to receive changes
                response = self.__select__(
                    # it is better to use an XPath query here to avoid an error if the element is not found (the element might be added later?)
                    QueryXPath(xpath=QueryXML.new_xpath(action.topic), attributes=[])
                )
                response.action_id = action.id
                if not response.values:
                    _LOGGER.warning(
                        "%s subscribed to element: `%s` that does not currently exist in the xml document.",
                        action.subscriber,
                        action.topic,
                    )
                return response

            elif isinstance(action, UnsubscribeXMLElementChange):
                self._xml_element_change_publisher.unsubscribe(
                    action.topic, action.subscriber
                )
            else:
                raise TypeError(f"Unknown subscription type: {type(action)}")
            return ActiveObservation(action_id=action)

    return XMLChangeAmbient
