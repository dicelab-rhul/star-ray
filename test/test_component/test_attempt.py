# pylint: disable=E1101
from star_ray.agent import ActiveActuator, attempt
from star_ray.event import MouseButtonEvent, KeyEvent


class MyComponent(ActiveActuator):

    @attempt(route_events=[KeyEvent])
    def foo(self, action):
        return action


class MyComponent2(MyComponent):

    @attempt(route_events=[MouseButtonEvent])
    def bar(self, action):
        return action


c = MyComponent()
c.foo(1)
print(MyComponent.__attemptmethods__)

b = MyComponent2()
b.bar(2)
print(MyComponent2.__attemptmethods__)
