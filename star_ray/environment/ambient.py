from abc import ABCMeta, abstractmethod
import ray


class Ambient(metaclass=ABCMeta):
    def __init__(self, agents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._agents = agents

    def get_agents(self):
        return self._agents

    @abstractmethod
    def __select__(self, query):
        pass

    @abstractmethod
    def __update__(self, query):
        pass

    def kill(self):
        for agent in self._agents:
            if isinstance(agent, ray.actor.ActorHandle):
                ray.kill(agent, no_restart=True)
        self._agents.clear()
