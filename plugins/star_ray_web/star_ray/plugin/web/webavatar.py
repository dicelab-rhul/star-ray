from abc import abstractmethod
from typing import List, Any, Union
from star_ray import Agent, Event, ActiveSensor, ActiveActuator
import asyncio
import itertools


class _WebAvatar(Agent):

    @abstractmethod
    async def __receive__(self, data: bytes):
        pass

    @abstractmethod
    async def __send__(self) -> bytes:
        pass


class WebAvatar(_WebAvatar):
    """
    This is a simple implementation of a WebAvatar that runs according to the environment cycle,
    user actions are not immediately executed - the will be executed during this agents cycle (as managed by the environment).
    This may impact responsiveness, but in cases where the environment cycle is fast it is sufficient.
    TODO I will implement a more responsive version that runs independently of the environment cycle soon!
    """

    def __init__(self, *args, protocol_dtype="json", **kwargs):
        super().__init__(*args, **kwargs)
        self._observation_buffer = asyncio.Queue()
        self._action_buffer = asyncio.Queue()
        self._protocol_dtype = protocol_dtype

    @abstractmethod
    def attempt(self, action: Any):
        pass

    @abstractmethod
    def perceive(
        self, component: Union[ActiveSensor, ActiveActuator], observation: Event
    ) -> Any:
        pass

    async def __execute__(self, state, *args, **kwargs):
        return super().__execute__(state, *args, **kwargs)

    async def __sense__(self, state, *args, **kwargs):
        return super().__sense__(state, *args, **kwargs)

    async def __cycle__(self):
        await self.__perceive__()
        await self.__attempt__()

    async def __attempt__(self):
        actions = _get_all_recent(self._action_buffer)
        for action in actions:
            self.attempt(action)

    async def __perceive__(self):
        for component in itertools.chain(self.sensors, self.actuators):
            for observation in component.get_observations():
                data = self.perceive(component, observation)
                if data:
                    # TODO this might become problematic for sending json data... maybe we should just require that a list/tuple is returned
                    if not isinstance(data, (list, tuple)):
                        data = (data,)
                    for obs in data:
                        await self._observation_buffer.put(obs)

    async def __receive__(self, data: Any):
        return await self._action_buffer.put(data)

    async def __send__(self) -> Any:
        return await self._observation_buffer.get()


def _get_all_recent(queue: asyncio.Queue) -> List[Any]:
    items = []
    while True:
        try:
            items.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            break
    return items
