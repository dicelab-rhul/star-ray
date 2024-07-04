from star_ray.agent import Component, Sensor, Actuator, AgentRouted, observe
from star_ray.event import Event
from typing import List


class Event2(Event):
    pass


class StubState:

    def __select__(self, events):
        return events

    def __update__(self, events):
        return events


class MySensor(Sensor):

    def __sense__(self):
        return [Event(source=0), Event2()]


class MyActuator(Actuator):

    def __attempt__(self):
        return [Event(source=1)]


class MyAgent(AgentRouted):

    @observe([Event])
    def on_event(self, event: Event):
        print("on_event:", event)

    @observe([Event])
    def on_event_with_component(self, event: Event, component: Component):
        print("on_event_with_component:", event, component)

    @observe()
    def on_event_with_type_hint(self, event: Event | Event2, component: Component):
        print("on_event_with_type_hint:", event, component)


state = StubState()
agent = MyAgent([MySensor()], [MyActuator()])

agent.__execute__(state)  # end of previous cycle

agent.__sense__(state)
agent.__cycle__()
