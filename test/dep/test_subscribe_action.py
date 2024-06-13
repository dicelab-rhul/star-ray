from typing import Any
import ray
import ray.actor
from star_ray.pubsub import Subscribe, Unsubscribe
from star_ray.pubsub import Subscriber, TopicPublisher
from star_ray.event import Event

publisher = TopicPublisher()


class MySubscriber(Subscriber):
    def __notify__(self, message: Any) -> None:
        print("LOCAL", message)


sub1 = MySubscriber()

action = _SubscriptionActionBase(subscriber=sub1, topic=Event)

publisher.subscribe(action.topic, action.subscriber)
publisher.notify_subscribers(Event())

ray.init()


@ray.remote
class MyRemoteSubscriber(Subscriber):

    def __notify__(self, message: Any) -> None:
        print("REMOTE", message)

    def get_action(self):
        return _SubscriptionActionBase(subscriber=self, topic=Event)


sub2 = MyRemoteSubscriber.remote()
action = ray.get(sub2.get_action.remote())
print(action)

publisher.subscribe(action.topic, action.subscriber)
publisher.notify_subscribers(Event())
