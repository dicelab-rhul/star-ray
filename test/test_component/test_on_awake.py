from star_ray.agent import Agent, ActiveSensor, OnAwake
from types import SimpleNamespace


class MyAgent(Agent):
    def __cycle__(self):
        pass


@OnAwake
class MySensor(ActiveSensor):
    pass


agent = MyAgent([MySensor()], [])

state_stub = SimpleNamespace(select=lambda *args: None)

assert len(agent.sensors) == 1
agent.__sense__(state_stub)
# after second sense the sensor should have been removed
agent.__sense__(state_stub)
assert len(agent.sensors) == 0
