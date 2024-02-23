from abc import ABCMeta, abstractmethod
import ray

from star_ray.utils import new_uuid


class Ambient(metaclass=ABCMeta):
    def __init__(self, agents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = new_uuid()
        self._agents = agents

    @property
    def id(self):
        return self._id

    def get_id(self):
        return self.id

    @property
    def agents(self):
        return list(self._agents)

    def get_agents(self):
        return self.agents

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
