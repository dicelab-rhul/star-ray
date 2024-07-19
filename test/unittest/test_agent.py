"""Unit test `Agent` class."""

import unittest
from star_ray import Agent, Actuator, Sensor


class TestAgent(unittest.TestCase):
    """Unit tests for `Agent` class."""

    class MyActuator(Actuator):
        """Test actuator class."""

        def on_add(self, agent: Agent) -> None:  # noqa: D102
            return super().on_add(agent)

        def on_remove(self, agent: Agent) -> None:  # noqa: D102
            return super().on_remove(agent)

    class MySensor(Sensor):
        """Test actuator class."""

        def on_add(self, agent: Agent) -> None:  # noqa: D102
            return super().on_add(agent)

        def on_remove(self, agent: Agent) -> None:  # noqa: D102
            return super().on_remove(agent)

    class MyAgent(Agent):
        """Test agent class."""

        def __cycle__(self):  # noqa: D105
            pass

    def test_agent_setup(self):
        """Check the agent is set when sensors/actuators are attached."""
        sensor = self.MySensor()
        actuator = self.MyActuator()
        agent = self.MyAgent([sensor], [actuator])

        sensor2 = self.MySensor()
        agent.add_component(sensor2)
        actuator2 = self.MyActuator()
        agent.add_component(actuator2)

        self.assertEqual(sensor._agent, agent)
        self.assertEqual(actuator._agent, agent)
        self.assertEqual(sensor2._agent, agent)
        self.assertEqual(actuator2._agent, agent)

    # TODO test other agent methods!


if __name__ == "__main__":
    unittest.main()
