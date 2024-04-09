import asyncio
import itertools
from typing import List, Any
from star_ray.agent import Agent, Actuator, Sensor, RoutedActionAgent
from star_ray.event import ErrorResponse, SelectResponse, UpdateResponse
from star_ray.utils import _LOGGER

from star_ray.agent.component import Component
from .socket_handler import SocketHandler, SocketSerde


class WebAvatar(RoutedActionAgent, SocketHandler):
    """
    This implementation of an `Avatar` that runs according to the environment cycle, user actions are not immediately executed. They will be executed during this agents cycle (as managed by the environment). This has some impact on responsiveness if the environment cycle is slow.

    TODO I will implement a more responsive version that runs independently of the environment cycle soon!
    """

    def __init__(self, sensors, actuators, *args, serde: SocketSerde = None, **kwargs):
        super().__init__(sensors, actuators, *args, serde=serde, **kwargs)
        # this buffer is used to store events that should be sent to the user (observations)
        self._observation_buffer = asyncio.Queue()
        # this buffer is used to store events that have been received by the user (actions) e.g. mouse clicks
        self._action_buffer = asyncio.Queue()

    async def receive(self, data: Any):
        # here we add new incoming actions, these will be attempted during the agents cycle (see self.__attempt__)
        return await self._action_buffer.put(data)

    async def send(self) -> Any:
        # here we wait for new observations to be added to the buffer, this happens during the agents cycle (see self.__perceive__)
        return await self._observation_buffer.get()

    def __cycle__(self):
        self.__perceive__()
        actions = _get_all_recent(self._action_buffer)
        self.__attempt__(actions)

    def __perceive__(self):
        for component in itertools.chain(self.sensors, self.actuators):
            for observation in component.get_observations():
                if isinstance(observation, ErrorResponse):
                    # pylint: disable = E1128
                    observation = self.handle_error_response(component, observation)
                    if observation:
                        self._observation_buffer.put_nowait(observation)
                elif isinstance(observation, SelectResponse):
                    assert isinstance(component, Sensor)
                    # pylint: disable = E1128
                    observation = self.handle_sensor_response(component, observation)
                    if not observation is None:
                        # we want to raise an error here if there is no space.
                        # it probably means the events are coming in too fast and we need to adjust some settings...
                        self._observation_buffer.put_nowait(observation)
                elif isinstance(observation, UpdateResponse):
                    assert isinstance(component, Actuator)
                    # pylint: disable = E1128
                    observation = self.handle_actuator_response(component, observation)
                    if not observation is None:
                        self._observation_buffer.put_nowait(observation)

    def handle_error_response(self, component: Component, event: ErrorResponse):
        # by default we do not want to send these responses to the web server
        _LOGGER.warning(
            "%s received an %s with an internal error %s which was not handled. If the error is being handle, do not call `super()` in `handle_error_response`.",
            str(WebAvatar),
            str(type(event)),
            str(event.exception_type),
        )
        return None  # this means we fail silently

    def handle_actuator_response(self, component: Component, event: UpdateResponse):
        # by default we do not want to send these responses to the web server
        return None

    def handle_sensor_response(self, component: Component, event: SelectResponse):
        return event  # by default we want to send these responses to the web server


def _get_all_recent(queue: asyncio.Queue) -> List[Any]:
    items = []
    while True:
        try:
            items.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            break
    return items
