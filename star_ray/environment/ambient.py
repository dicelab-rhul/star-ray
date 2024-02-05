from abc import ABCMeta, abstractmethod
import ray


class Ambient(metaclass=ABCMeta):
    def __init__(self, agents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agents = agents

    def get_agents(self):
        return self.agents

    @abstractmethod
    def __query__(self, query):
        pass

    def kill(self):
        for agent in self.agents:
            if isinstance(agent, ray.actor.ActorHandle):
                ray.kill(agent, no_restart=True)
        self.agents.clear()
