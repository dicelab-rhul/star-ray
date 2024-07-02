from typing import Any, List, Union
from abc import ABC, abstractmethod
import ray

from ..utils import new_uuid, _Future
from ..agent import _Agent
from ..event import Event, Action, ActiveObservation, ErrorActiveObservation
from ..pubsub import Subscribe, Unsubscribe


class Ambient(ABC):

    def __init__(self, agents, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = new_uuid()
        agents = [_Agent.new(agent) for agent in agents]
        self._agents = {agent.get_id(): agent for agent in agents}
        self._is_alive = False

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

    async def __terminate__(self, state: "_Ambient"):
        self._is_alive = False
        agents = list(self.get_agents())
        self._agents.clear()
        # TODO if an agent takes too long, then just cancel it?
        await _Future.gather([agent.__terminate__(state) for agent in agents])

    async def __initialise__(self, state: "_Ambient"):
        self._is_alive = True
        # TODO if an agent takes too long, then just cancel it?
        agents = list(self.get_agents())
        await _Future.gather([agent.__initialise__(state) for agent in agents])

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


class _Ambient(ABC):

    @staticmethod
    def new(ambient: Union[Ambient, ray.actor.ActorHandle]) -> "_Ambient":
        if isinstance(ambient, ray.actor.ActorHandle):
            return _AmbientRemote(ambient)
        elif isinstance(ambient, Ambient):
            return _AmbientLocal(ambient)
        else:
            raise TypeError(type(ambient))

    @property
    @abstractmethod
    def is_alive(self):
        pass

    @abstractmethod
    async def __initialise__(self):
        pass

    @abstractmethod
    async def __terminate__(self):
        pass

    @abstractmethod
    def __subscribe__(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def __update__(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def __select__(self, actions: List[Event]) -> List[Any]:
        pass

    @abstractmethod
    def get_agents(self) -> List[_Agent]:
        pass


class _AmbientRemote(_Ambient):

    def __init__(self, ambient: ray.actor.ActorHandle):
        super().__init__()
        self._inner = ambient

    @property
    def is_alive(self):
        return self._inner.get_is_alive.remote()

    async def __initialise__(self):
        return await self._inner.__initialise__.remote(self)

    async def __terminate__(self):
        return await self._inner.__terminate__.remote(self)

    def __subscribe__(self, actions: List[Subscribe | Unsubscribe]) -> List[Any]:
        return [self._inner.__subscribe__.remote(query) for query in actions]

    def __update__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__update__.remote(query) for query in actions]

    def __select__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__select__.remote(query) for query in actions]

    def get_agents(self) -> List[_Agent]:
        return ray.get(self._inner.get_agents.remote())


class _AmbientLocal(_Ambient):

    def __init__(self, ambient: Ambient):
        super().__init__()
        self._inner = ambient

    @property
    def is_alive(self):
        return self._inner.get_is_alive()

    async def __initialise__(self):
        return await self._inner.__initialise__(self)

    async def __terminate__(self):
        return await self._inner.__terminate__(self)

    def __subscribe__(self, actions: List[Subscribe | Unsubscribe]) -> List[Any]:
        return [self._inner.__subscribe__(query) for query in actions]

    def __update__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__update__(query) for query in actions]

    def __select__(self, actions: List[Event]) -> List[Any]:
        return [self._inner.__select__(query) for query in actions]

    def get_agents(self) -> List[_Agent]:
        return self._inner.get_agents()
