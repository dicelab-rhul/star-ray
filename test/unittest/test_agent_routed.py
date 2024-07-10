from star_ray.agent import Component, Sensor, Actuator, AgentRouted, observe, attempt, decide
from star_ray.event import Event
from typing import List


class EventA(Event):
    pass


class EventB(EventA):
    pass


class EventC(Event):
    pass


class StubState:

    def __select__(self, events):
        return events

    def __update__(self, events):
        return events


class MySensor(Sensor):

    def __sense__(self):
        return [EventC(), EventA()]


class MyActuator(Actuator):

    def __attempt__(self):
        return [EventA()]

    @attempt
    def take1(self, action: Event):
        print(f"take1 {type(action)}")
        return action

    @attempt()
    def take2(self, action: EventA):
        print(f"take2 {type(action)}")
        return action

    @attempt()
    def take3(self, action: EventA | EventC):
        print(f"take3 {type(action)}")
        return action

    @attempt([EventA, EventC])
    def take4(self, action):
        print(f"take4 {type(action)}")
        return action


class MyAgent(AgentRouted):

    @observe([EventA])
    def on_event(self, event: EventA):
        print("on_event:", event)

    @observe([EventA])
    def on_event_with_component(self, event: EventA, component: Component):
        print("on_event_with_component:", event, component)

    @observe()
    def on_event_with_type_hint(self, event: EventA | EventC, component: Component):
        print("on_event_with_type_hint:", event, component)

    @decide
    def decideA(self):
        print("decide A")
        return [EventA()]

    @decide()
    def decideB(self):
        print("decide B")
        return [EventB()]

    @decide()
    def decideC(self):
        print("decide C")
        return [EventC()]


state = StubState()
agent = MyAgent([MySensor()], [MyActuator()])

agent.__execute__(state)  # end of previous cycle
agent.__sense__(state)
agent.__cycle__()

# agent.__execute__(state)
