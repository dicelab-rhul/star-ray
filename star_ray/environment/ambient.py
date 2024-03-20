from typing import Any, List

from abc import ABC, abstractmethod
from ..utils import new_uuid

from ..agent import _Agent


class Ambient(ABC):

    def __init__(self, agents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = new_uuid()
        agents = [_Agent.new(agent) for agent in agents]
        self._agents = {agent.id: agent for agent in agents}

    def add_agent(self, agent: Any) -> _Agent:
        agent = _Agent.new(agent)
        # TODO we need to explicitly prevent remote agents if the ambient is not remote itself
        # otherwise the agent will be modifying a copy of the ambient!
        agent_id = agent.id
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already exists in ambient {self.id}.")
        self._agents[agent_id] = agent
        return agent

    def remove_agent(self, agent: Any):
        agent = _Agent.new(agent)
        agent_id = agent.id
        del self._agents[agent_id]
        agent.kill()

    @property
    def id(self):
        return self._id

    def get_id(self):
        return self.id

    @property
    def agents(self) -> List[_Agent]:
        return list(self._agents.values())

    def get_agents(self) -> List[_Agent]:
        return self.agents

    def kill(self):
        for agent in self._agents.values():
            agent.kill()
        self._agents.clear()

    @abstractmethod
    def __select__(self, action):
        pass

    @abstractmethod
    def __update__(self, action):
        pass
