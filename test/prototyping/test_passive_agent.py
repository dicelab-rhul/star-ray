import os

os.environ["RAY_DEDUP_LOGS"] = "0"
from pprint import pprint

import ray

ray.init()

from star_ray.agent import Agent, Sensor, Actuator


class MyPassiveSensor(Sensor):
    def __sense__(self):
        return [("sense", 0)]


class MyPassiveActuator(Actuator):
    def __attempt__(self):
        return [("attempt", 1)]


@ray.remote
class MyAgent(Agent):
    def __cycle__(self):
        print(
            f"agent {self.id}",
            f"\n  sensor percepts:   { {sensor.id: sensor.get() for sensor in self.sensors} }",
            f"\n  actuator percepts: { {actuator.id: actuator.get() for actuator in self.actuators} }",
        )


@ray.remote
class Ambient:
    def __init__(self, agents):
        self.agents = agents
        self.state = 0

    def get_agents(self):
        return self.agents

    def __query__(self, query):
        if query[0] == "sense":
            return self.state
        elif query[0] == "attempt":
            self.state += query[1]
            return True
        else:
            print("ERROR : invalid query:", query)


class Environment:
    def __init__(self, agents):
        self.ambient = Ambient.remote(agents)

    def step(self):
        agents = ray.get(self.ambient.get_agents.remote())
        refs = [agent.__sense__.remote(self.ambient) for agent in agents]
        # wait for sense to complete - perhaps use ray.wait instead
        _ = [ray.get(ref) for ref in refs]

        refs = [agent.__cycle__.remote() for agent in agents]
        # wait for cycle to complete - perhaps use ray.wait instead
        _ = [ray.get(ref) for ref in refs]

        refs = [agent.__execute__.remote(self.ambient) for agent in agents]
        # wait for execute to complete - perhaps use ray.wait instead
        _ = [ray.get(ref) for ref in refs]


N = 3

sensors = [MyPassiveSensor() for i in range(N)]
actuators = [MyPassiveActuator() for i in range(N)]
agents = [
    MyAgent.remote([sensor], [actuator]) for sensor, actuator in zip(sensors, actuators)
]

environment = Environment(agents)
environment.step()
environment.step()
