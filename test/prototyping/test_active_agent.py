import os
import logging
import random

logger = logging.getLogger("ray")
os.environ["RAY_DEDUP_LOGS"] = "0"

import ray

ray.init()

from star_ray.agent import Agent, Sensor, Actuator


class MyActiveActuator(Actuator):
    @Actuator.action
    def attempt_1(self):
        return ("attempt", 1)

    @Actuator.action
    def attempt_2(self):
        return ("attempt", 2)


class MyActiveSensor(Sensor):
    @Sensor.action
    def sense_1(self):
        return ("sense", 0)

    @Sensor.action
    def sense_2(self):
        return ("sense", 1)


@ray.remote
class MyAgent(Agent):
    def sense(self, sensor):
        if random.uniform(0, 1) > 0.5:
            sensor.sense_1()
        else:
            sensor.sense_2()

    def execute(self, actuator):
        if random.uniform(0, 1) > 0.5:
            actuator.attempt_1()
        else:
            actuator.attempt_2()

    def __cycle__(self):
        print(
            f"agent {self.id}",
            f"\n  sensor percepts:   { {sensor.id: sensor.get() for sensor in self.sensors} }",
            f"\n  actuator percepts: { {actuator.id: actuator.get() for actuator in self.actuators} }",
        )
        # it would also be possible to call the various action methods (sense_1, sense_2, attempt_1, attempt_2) here.
        # self.sense is called before __cycle__ so that an initial perception is ready, but it does not need to be implemented by an agent.


@ray.remote
class Ambient:
    def __init__(self, agents):
        self.agents = agents
        self.state = [0, "test"]

    def get_agents(self):
        return self.agents

    def __query__(self, query):
        print(query)
        if query[0] == "sense":
            return self.state[query[1]]
        elif query[0] == "attempt":
            self.state[0] += query[1]
            return True
        else:
            print("ERROR : invalid query:", query)


class Environment:
    def __init__(self, agents):
        self.ambient = Ambient.remote(agents)

    def step(self):
        agents = ray.get(self.ambient.get_agents.remote())
        refs = [agent.__sense__.remote(self.ambient) for agent in agents]
        # wait for sense to complete - TODO perhaps use ray.wait instead
        _ = [ray.get(ref) for ref in refs]

        refs = [agent.__cycle__.remote() for agent in agents]
        # wait for cycle to complete - TODO perhaps use ray.wait instead
        _ = [ray.get(ref) for ref in refs]

        refs = [agent.__execute__.remote(self.ambient) for agent in agents]
        # wait for execute to complete - TODO perhaps use ray.wait instead
        _ = [ray.get(ref) for ref in refs]


N = 2

sensors = [MyActiveSensor() for i in range(N)]
actuators = [MyActiveActuator() for i in range(N)]
agents = [
    MyAgent.remote([sensor], [actuator]) for sensor, actuator in zip(sensors, actuators)
]

environment = Environment(agents)
environment.step()
environment.step()
