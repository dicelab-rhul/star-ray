import unittest
from star_ray.agent import Actuator, Sensor, attempt
from star_ray.event import Event
from unittest.mock import MagicMock


class MyActuator(Actuator):

    @attempt()
    def foo(self, action):
        return action


class MySensor(Sensor):

    @attempt()
    def bar(self, action):
        return action


class TestComponents(unittest.TestCase):

    def test_sensor_cycle(self):
        state = MagicMock()
        observation = Event()
        action = Event()
        state.__select__ = lambda _: [observation]
        sensor = MySensor()
        a = sensor.bar(action)
        self.assertEqual(action, a)
        sensor.__query__(state)
        o = list(sensor.iter_observations())[0]
        self.assertEqual(observation, o)

    def test_actuator_cycle(self):
        state = MagicMock()
        observation = Event()
        action = Event()
        state.__update__ = lambda _: [observation, observation]
        actuator = MyActuator()
        a = actuator.foo(action)
        self.assertEqual(action, a)
        actuator.__query__(state)
        os = list(actuator.iter_observations())
        self.assertEqual(observation, os[0])
        self.assertEqual(observation, os[1])


if __name__ == "__main__":
    unittest.main()
