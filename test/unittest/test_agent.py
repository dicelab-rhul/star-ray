from star_ray import Agent, Actuator, Sensor


class MyActuator(Actuator):

    def on_add(self, agent: Agent) -> None:
        return super().on_add(agent)

    def on_remove(self, agent: Agent) -> None:
        return super().on_remove(agent)


class MySensor(Sensor):

    def on_add(self, agent: Agent) -> None:
        return super().on_add(agent)

    def on_remove(self, agent: Agent) -> None:
        return super().on_remove(agent)


class MyAgent(Agent):

    def __cycle__(self):
        pass


sensor = MySensor()
actuator = MyActuator()
agent = MyAgent([sensor], [actuator])

assert sensor._agent == agent
assert actuator._agent == agent
