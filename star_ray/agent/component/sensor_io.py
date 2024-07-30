"""Module defines the `IOSensor` which represents a senors that gets its observations from a device. These sensors do not read the environment state, instead they may read a file, grab user input, or perform some other IO READ operation."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from ...event import Event
from .sensor import Sensor

if TYPE_CHECKING:
    from ..agent import Agent
    from ...environment import State


class IOSensor(Sensor):
    """Base class for sensors whose observations are obtained from an IO device or stream. This may be a file, user input stream, or other IO device/stream.

    The sensor wraps an IO device and assumes it defines the following methods:
    - `get_nowait() -> list[Event]`
    - `start()` -> None`
    - `stop()` -> None`

    `get_nowait()` will be used to get observations at each cycle of the sensor.

    TODO an async `get() -> list[Event]` method?
    TODO perhaps use the __enter__ __exit__ pattern instead? this is more commonly defined by IO devices (e.g. files).
    TODO implement a wrapper for files and pipes (it would be nice if we could read from file streams/os pipes)
    """

    def __init__(self, device: Any):
        """Constructor.

        Args:
            device (Any): io device that will provide observations (Event) to the sensor via `get_nowait` or `get`.
        """
        super().__init__()
        # the device must contain this method TODO a more indepth check
        assert hasattr(device, "get_nowait")
        self._device = device

    def __query__(self, _: State) -> None:  # noqa
        # we query from the device, not from the state
        observations: list[Event] = self._device.get_nowait()
        # preprocess the observations ready to be received by the agent
        self._observations.push_all(self.__transduce__(observations))

    def on_add(self, agent: Agent) -> None:  # noqa
        super().on_add(agent)
        start = getattr(self._device, "start", None)
        if start:
            start()

    def on_remove(self, agent: Agent) -> None:  # noqa
        super().on_remove(agent)
        stop = getattr(self._device, "stop", None)
        if stop:
            stop()
