"""Unit tests for the `TypePublisher` class, this class is an important one in star_ray pub-sub."""

import unittest
from typing import Any
from star_ray.pubsub import TypePublisher, Subscriber


class A:  # noqa: D101
    pass


class B(A):  # noqa: D101
    pass


class C(A):  # noqa: D101
    pass


class D(B, C):  # noqa: D101
    pass


class E:  # noqa: D101
    pass


class TestTypePublisher(unittest.TestCase):
    """TypePublisher unit tests."""

    def test_type_publisher(self):
        """Does it publish with a single subscribed type?"""
        PUBLISHER = TypePublisher()

        class MySubscriber(Subscriber):
            def __init__(self, topic: type):
                self._topic = topic
                PUBLISHER.subscribe(self._topic, self)
                self._calls = []

            def __notify__(self, message: Any) -> None:
                self._calls.append(type(message))

        subscriber1 = MySubscriber(A)
        subscriber2 = MySubscriber(E)

        PUBLISHER.publish(A())
        PUBLISHER.publish(B())
        PUBLISHER.publish(C())
        PUBLISHER.publish(D())
        PUBLISHER.publish(E())

        self.assertListEqual(subscriber1._calls, [A, B, C, D])
        self.assertListEqual(subscriber2._calls, [E])

    def test_type_publisher_multi(self):
        """Does it publish with multiple subscribed types?"""
        PUBLISHER = TypePublisher()

        class MySubscriber(Subscriber):
            def __init__(self, topic: list[type]):
                for t in topic:
                    PUBLISHER.subscribe(t, self)
                self._calls = []

            def __notify__(self, message: Any) -> None:
                self._calls.append(type(message))

        subscriber1 = MySubscriber([A, C])

        PUBLISHER.publish(A())
        PUBLISHER.publish(B())
        PUBLISHER.publish(C())
        PUBLISHER.publish(D())
        PUBLISHER.publish(E())
        self.assertListEqual(subscriber1._calls, [A, B, C, D])


if __name__ == "__main__":
    unittest.main()
