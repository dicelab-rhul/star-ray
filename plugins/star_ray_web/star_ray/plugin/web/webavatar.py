import asyncio
from typing import List, Any
from star_ray.agent import Actuator, Sensor, RoutedActionAgent
from star_ray.event import ErrorObservation, Observation
from star_ray.utils import _LOGGER
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
        for component in self.actuators:
            for observation in component.iter_observations():
                # pylint: disable = E1128
                observation = self.handle_actuator_observation(component, observation)
                if not observation is None:
                    self._observation_buffer.put_nowait(observation)

        for component in self.sensors:
            for observation in component.iter_observations():
                # pylint: disable = E1128
                observation = self.handle_sensor_observation(component, observation)
                if not observation is None:
                    self._observation_buffer.put_nowait(observation)

    def handle_actuator_observation(
        self, actuator: Actuator, event: Observation
    ) -> Any:
        _check_error_observation(event)
        # by default we do not want to send these responses to the web server
        return None

    def handle_sensor_observation(self, sensor: Sensor, event: Observation) -> Any:
        _check_error_observation(event)
        # by default we want to send these responses to the web server
        return event


def _check_error_observation(event: Observation):
    if isinstance(event, ErrorObservation):
        _LOGGER.warning(
            "%s received an %s with an internal error %s which was not handled. If the error is being handle, do not call `super()`",
            str(WebAvatar),
            str(type(event)),
            str(event.exception_type),
        )


def _get_all_recent(queue: asyncio.Queue) -> List[Any]:
    items = []
    while True:
        try:
            items.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            break
    return items
