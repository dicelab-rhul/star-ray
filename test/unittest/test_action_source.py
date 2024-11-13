"""Test case for action source - the source of an actio is composed of the ID of the agent and the executing component, this should be recoverable."""

import unittest
from star_ray.agent import Agent, Sensor, Actuator, Component
from star_ray.event import Action


class MyAgent(Agent):  # noqa
    def __cycle__(self):  # noqa
        pass


# unit test for action id
class TestActionId(unittest.TestCase):
    """Testing action source."""

    def test_action_source(self):
        """Test action source."""
        sensor = Sensor()
        actuator = Actuator()
        agent = MyAgent([], [])
        agent.add_component(sensor)
        agent.add_component(actuator)
        action = Action()
        Component.set_action_source(sensor, [action])
        component_id, agent_id = Component.unpack_source(action)
        self.assertEqual(component_id, sensor.id)
        self.assertEqual(agent_id, agent.id)

        action = Action()
        Component.set_action_source(actuator, [action])
        component_id, agent_id = Component.unpack_source(action)
        self.assertEqual(component_id, actuator.id)
        self.assertEqual(agent_id, agent.id)


if __name__ == "__main__":
    unittest.main()
