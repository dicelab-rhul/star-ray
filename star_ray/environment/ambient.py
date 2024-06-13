from typing import Any, List
import asyncio
from abc import ABC, abstractmethod
from ..utils import new_uuid

from ..agent import _Agent
from ..event import Action, ActiveObservation, ErrorActiveObservation
from ..pubsub import Subscribe, Unsubscribe


class Ambient(ABC):

    def __init__(self, agents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = new_uuid()
        agents = [_Agent.new(agent) for agent in agents]
        self._agents = {agent.get_id(): agent for agent in agents}
        self._is_alive = True

    def add_agent(self, agent: Any) -> _Agent:
        agent = _Agent.new(agent)
        # TODO we need to explicitly prevent remote agents if the ambient is not remote itself
        # otherwise the agent will be modifying a copy of the ambient!
        agent_id = agent.get_id()
        if agent_id in self._agents:
            raise ValueError(
                f"Agent {agent_id} already exists in ambient {self.get_id()}."
            )
        self._agents[agent_id] = agent
        return agent

    def remove_agent(self, agent: Any):
        agent = _Agent.new(agent)
        agent_id = agent.get_id()
        del self._agents[agent_id]
        agent.__terminate__()

    @property
    def is_alive(self):
        return self._is_alive

    @property
    def id(self):
        return self._id

    def get_is_alive(self):
        return self._is_alive

    def get_id(self):
        return self._id

    def get_agents(self) -> List[_Agent]:
        return list(self._agents.values())

    def __terminate__(self):
        for agent in self._agents.values():
            agent.__terminate__()
        self._agents.clear()
        self._is_alive = False

    # TODO does this need to be async?
    async def __initialise__(self):
        pass

    @abstractmethod
    def __select__(self, action: Action) -> ActiveObservation | ErrorActiveObservation:
        pass

    @abstractmethod
    def __update__(self, action: Action) -> ActiveObservation | ErrorActiveObservation:
        pass

    @abstractmethod
    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:
        pass
