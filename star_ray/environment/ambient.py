"""Module defines the `Ambient` class. This class encapsulates the state of the environment, see the class docs for details."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING
from abc import ABC, abstractmethod
import ray

from ..utils import int64_uuid, _Future
from ..agent import _Agent
from ..event import Event, Action, ActiveObservation, ErrorActiveObservation
from ..pubsub import Subscribe, Unsubscribe

if TYPE_CHECKING:
    from ..agent import Agent


class Ambient(ABC):
    """Base class for `Ambient` implementations.

    The `Ambient` is contains the state of the environment, that is, it contains all variables (or data) that are accessible and manipulable by the agents present in the given environment. The ambient also contains references to all of the agents that are present in the environment.

    All ambients must implement two key methods: `__select__` and `__update__`.

    `__select__` is a read-only operation which takes an `Action` and will return an `Observation`. The `Action` typically defines what data the agent is interested in observing, and the `Observation` will contain this data. These actions will originate exclusively from the agents `Sensor`s and are executed during the `__sense__` step in the agents cycle.

    `__update__` is a write operation which also takes an `Action` and may return an `Observation`. The `Action` defines how the environments state (the `Ambient`) will be mutated. These actions will originate exclusively from the agents `Actuator`s and are executed during the `__execute__` step in the agents cycle.

    Another important method `__subscribe__` is used to handle actions that are specifically related to `star_ray`s pub-sub mechansim. Not all ambients need implement this.

    Agents can be added or removed from the environent via corresponding methods in the `Ambient`.
    """

    def __init__(self, agents: list[Agent], *args, **kwargs):
        """Constructor.

        Args:
            agents (list[Agent]): a list of agents that will initially be added to this `Ambient`.
            args (list[Any]): optional additional arguments.
            kwargs (dict[str, Any]): optional additional arguments.
        """
        super().__init__(*args, **kwargs)
        self._id = int64_uuid()
        agents = [_Agent.new(agent) for agent in agents]
        self._agents = {agent.get_id(): agent for agent in agents}
        self._is_alive = False

    def add_agent(self, agent: Agent) -> _Agent:
        """Adds a new agent to this ambient.

        Args:
            agent (Any): the agent to add

        Raises:
            ValueError: if the agent already exists.

        Returns:
            _Agent: A handle (and wrapper) to the added agent.
        """
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

    def remove_agent(self, agent: Agent) -> None:
        """Removes an agent from this `Ambient`. This has the side effect of terminating the agent (via `Agent.__terminate__`).

        Args:
            agent (Agent): the agent to remove.

        """
        agent = _Agent.new(agent)
        agent_id = agent.get_id()
        del self._agents[agent_id]
        agent.__terminate__()

    @property
    def is_alive(self) -> bool:
        """Whether this `Ambient` is currently alive - otherwise it has shutdown (via `__terminate__`) and all agents have either terminated or are in the process of terminating. This will also return False if the `Ambient` has not yet been initialised via `__initialise__`.

        Returns:
            bool: whether this ambient is alive.
        """
        return self._is_alive

    @property
    def id(self) -> int:
        """The id of this `Ambient`.

        Returns:
            int : the unique identifier of this `Ambient`.
        """
        return self._id

    def get_is_alive(self) -> bool:
        """Getter for `is_alive`, see property for details.

        Returns:
            bool: whether this ambient is alive.
        """
        return self._is_alive

    def get_id(self) -> int:
        """Getter for `id`, see property for details.

        Returns:
            int: the unique identifier of this `Ambient`
        """
        return self._id

    def get_agents(self) -> list[_Agent]:
        """Getter for all agents that are currently present in this `Ambient`. This is read-only and modifications to the returned list will have no effect. If you want to add or remove an agent use the corresponding methods.

        Returns:
            list[_Agent]: list of agents.
        """
        return list(self._agents.values())

    def get_agent_count(self) -> int:
        """Get the number of agents currently in this ambient."""
        return len(self._agents)

    async def __terminate__(self) -> None:
        """Terminate this `Ambient`. After this call `is_alive` will return False. This call will wait for all agents to be terminated via their `__terminate__` method."""
        state = _Ambient.new(self)
        self._is_alive = False
        agents = list(self.get_agents())
        self._agents.clear()
        # TODO if an agent takes too long, then just cancel it?
        await _Future.gather([agent.__terminate__(state) for agent in agents])

    async def __initialise__(self) -> None:
        """Initialise this `Ambient`. After this call `is_alive` will return True. This call will wait for all agents to initialise via their `__initialise__` method."""
        self._is_alive = True
        state = _Ambient.new(self)
        # TODO if an agent takes too long, then just cancel it?
        agents = list(self.get_agents())
        await _Future.gather([agent.__initialise__(state) for agent in agents])

    @abstractmethod
    def __select__(self, action: Action) -> ActiveObservation | ErrorActiveObservation:
        """A read-only operation which takes an `Action` and will return an `Observation`. The `Action` typically defines what data the agent is interested in observing, and the `Observation` will contain this data. These actions will originate exclusively from the agents `Sensor`s and are executed during the `__sense__` step in the agents cycle. This method may be called manually (especially when dealing with actions/observations in a subclass of `Ambient`, `Environment` or `Sensor`.

        Args:
            action (Action): the sense action

        Returns:
            ActiveObservation | ErrorActiveObservation: the resulting observation
        """
        pass

    @abstractmethod
    def __update__(
        self, action: Action
    ) -> ActiveObservation | ErrorActiveObservation | None:
        """A write operation which also takes an `Action` and may return an `Observation`. The `Action` defines how the environments state (this `Ambient`) will be mutated. These actions will originate exclusively from the agents `Actuator`s and are executed during the `__execute__` step in the agents cycle. This method may be called manually (especially when dealing with actions/observations in a subclass of `Ambient`, `Environment` or `Actuator`.

        Args:
            action (Action): the action

        Returns:
            ActiveObservation | ErrorActiveObservation | None: the resulting observation (or None)
        """
        pass

    def __subscribe__(
        self, action: Subscribe | Unsubscribe
    ) -> ActiveObservation | ErrorActiveObservation:
        """Handles subcriptions to events in this ambient if the `Ambient` supports pub-sub. By default this does nothing. If you are considering implementing pub-sub functionality, see the `star_ray.pubsub` sub-package for details.

        Typically, this method will be called from `__select__` as `Sensor`s are often interested subscribing to receive certain events are observations. It is also possible (but unusual) to call this from `__update__`

        Args:
            action (Subscribe | Unsubscribe): the subscription action

        Returns:
            ActiveObservation | ErrorActiveObservation: an observation typically indicating whether the subscription was successful
        """
        pass


class _Ambient(ABC):
    @staticmethod
    def new(ambient: Ambient | ray.actor.ActorHandle) -> _Ambient:
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
    def __subscribe__(self, actions: list[Event]) -> list[Any]:
        pass

    @abstractmethod
    def __update__(self, actions: list[Event]) -> list[Any]:
        pass

    @abstractmethod
    def __select__(self, actions: list[Event]) -> list[Any]:
        pass

    @abstractmethod
    def get_agents(self) -> list[_Agent]:
        pass

    @abstractmethod
    def get_agent_count(self) -> int:
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

    def __subscribe__(self, actions: list[Subscribe | Unsubscribe]) -> list[Any]:
        return [self._inner.__subscribe__.remote(query) for query in actions]

    def __update__(self, actions: list[Event]) -> list[Any]:
        return [self._inner.__update__.remote(query) for query in actions]

    def __select__(self, actions: list[Event]) -> list[Any]:
        return [self._inner.__select__.remote(query) for query in actions]

    def get_agents(self) -> list[_Agent]:
        return ray.get(self._inner.get_agents.remote())

    def get_agent_count(self) -> int:
        return ray.get(self._inner.get_agent_count.remote())


class _AmbientLocal(_Ambient):
    def __init__(self, ambient: Ambient):
        super().__init__()
        self._inner = ambient

    @property
    def is_alive(self):
        return self._inner.get_is_alive()

    async def __initialise__(self):
        return await self._inner.__initialise__()

    async def __terminate__(self):
        return await self._inner.__terminate__()

    def __subscribe__(self, actions: list[Subscribe | Unsubscribe]) -> list[Any]:
        return [self._inner.__subscribe__(query) for query in actions]

    def __update__(self, actions: list[Event]) -> list[Any]:
        return [self._inner.__update__(query) for query in actions]

    def __select__(self, actions: list[Event]) -> list[Any]:
        return [self._inner.__select__(query) for query in actions]

    def get_agents(self) -> list[_Agent]:
        return self._inner.get_agents()

    def get_agent_count(self) -> int:
        return self._inner.get_agent_count()
