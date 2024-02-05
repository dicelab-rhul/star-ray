import os
import logging

logger = logging.getLogger("ray")
os.environ["RAY_DEDUP_LOGS"] = "0"

import ray

ray.init()


@ray.remote
class Agent:
    def __init__(self, sensors, actuators):
        self.sensors = sensors
        self.actuators = actuators

    def cycle(self, environment):
        for sensor in self.sensors:
            sensor.__sense__(environment)
        self.decide()
        for actuator in self.actuators:
            actuator.__attempt__(environment)

        # generally we should wait for each sense/attempt query to complete before returning
        # this will ensure that the agent does not sense again before its prior actions have completed.
        for sensor, actuator in zip(self.sensors, self.actuators):
            _, _ = sensor.get(), actuator.get()

    def decide(self):
        for actuator in self.actuators:
            # sometimes a result might be given after executing an action
            print("actuator response", actuator.get())
        for sensor in self.sensors:
            # get perceptions
            print("sensor response", sensor.sense())

        for actuator in self.actuators:
            actuator.attempt(1)


class Component:
    def __init__(self):
        self._result = None

    def __query__(self, environment, query):
        self._result = environment.query.remote(query)

    def get(self):
        if not isinstance(self._result, ray.ObjectRef):
            return self._result
        else:
            return ray.get(self._result)


class Sensor(Component):
    def __sense__(self, environment):
        query = "sense"
        super().__query__(environment, query)

    def sense(self):
        return self.get()


class Actuator(Component):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._action = None

    def __attempt__(self, environment):
        query = ("attempt", self._action)
        super().__query__(environment, query)

    def attempt(self, *args, **kwargs):
        self._action = args


@ray.remote
class Ambient:
    def __init__(self, agents):
        self.agents = agents
        self.state = 0

    def get_agents(self):
        return self.agents

    def query(self, query):
        if query == "sense":
            return self.state
        elif query[0] == "attempt":
            self.state += query[1][0]
            return True
        else:
            print("ERROR : invalid query:", query)


class Environment:
    def __init__(self, agents):
        self.ambient = Ambient.remote(agents)

    def step(self):
        agents = ray.get(self.ambient.get_agents.remote())
        # this is the simplest kind of synchronous step, it waits for all agents to finish their cycles before proceeding to the next cycle.
        handles = [agent.cycle.remote(self.ambient) for agent in agents]
        _ = [ray.get(handle) for handle in handles]


N = 1

sensors = [Sensor(f"sensor-{i}") for i in range(N)]
actuators = [Actuator(f"actuator-{i}") for i in range(N)]
agents = [
    Agent.remote([sensor], [actuator]) for sensor, actuator in zip(sensors, actuators)
]

environment = Environment(agents)
environment.step()
environment.step()
