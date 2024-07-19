"""Unit test for `AgentRouted` class."""

import unittest

from star_ray.agent import (
    Component,
    Sensor,
    Actuator,
    AgentRouted,
    observe,
    attempt,
    decide,
)
from star_ray.event import Event


class EventA(Event):  # noqa: D101
    pass


class EventB(EventA):  # noqa: D101
    pass


class EventC(Event):  # noqa: D101
    pass


class StubState:
    """Stub for the `Ambient` given that will be given to actuators/sensors."""

    def __select__(self, events):  # noqa: D105
        return events

    def __update__(self, events):  # noqa: D105
        return events


class MySensor(Sensor):
    """Test Sensor."""

    def __sense__(self):  # noqa: D105
        return [EventC(), EventA()]


class MyActuator(Actuator):
    """Test Actuator."""

    @attempt
    def take1(self, action: Event):  # noqa: D102
        return action


class MyAgent(AgentRouted):
    """Test Agent."""

    def __init__(self, sensors, actuators, *args, **kwargs):  # noqa: D107
        super().__init__(sensors, actuators, *args, **kwargs)
        self.events = []

    @observe([EventA])
    def on_event(self, event):
        """Should be called on eventA."""
        self.events.append(("default", type(event), None))

    @observe([EventA])
    def on_event_with_component(self, event: EventA, component: Component):
        """Should be called on eventA, with the correct component argument."""
        self.events.append(("with_component", type(event), type(component)))

    @observe()
    def on_event_with_type_hint(self, event: EventA | EventC, component: Component):
        """Should be called on eventA or EventC, with the correct component argument."""
        self.events.append(("with_type_hint", type(event), type(component)))

    @decide
    def decideA(self):  # noqa: D102
        return [EventA()]


class TestAgentRouted(unittest.TestCase):
    """Test AgentRouted."""

    def test_agent_cycle(self):
        """Test the cycle of the RoutedAgent, the @decide and @observe methods should all be called."""
        state = StubState()
        actuator = MyActuator()
        agent = MyAgent([MySensor()], [actuator])

        # Execute the agent's cycle
        agent.__sense__(state)  # sense - take EventC and EventA
        agent.__cycle__()

        # first sense event is EventC which triggers only with_type_hint
        self.assertEqual(agent.events[0], ("with_type_hint", EventC, MySensor))

        # second sense event is EventA
        self.assertEqual(agent.events[1], ("default", EventA, None))
        self.assertEqual(agent.events[2], ("with_component", EventA, MySensor))
        self.assertEqual(agent.events[3], ("with_type_hint", EventA, MySensor))
        agent.events.clear()

        # after decide!
        agent.__execute__(state)
        agent.__sense__(state)  # sense - take EventC and EventA
        agent.__cycle__()

        # these result from the decision and concern the actuator observations
        self.assertEqual(agent.events[0], ("default", EventA, None))
        self.assertEqual(agent.events[1], ("with_component", EventA, MyActuator))
        self.assertEqual(agent.events[2], ("with_type_hint", EventA, MyActuator))


if __name__ == "__main__":
    unittest.main()
