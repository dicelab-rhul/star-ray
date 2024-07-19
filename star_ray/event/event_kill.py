"""Module defines the `KillEvent` class, which is used to terminate an agent. See class documentation for details."""

from pydantic import model_validator, Field
from typing import ClassVar
from .event import Event
from ..utils import int64_uuid


# TODO untested
class KillEvent(Event):
    """Event that will kill an agent given its `id` (trigger a call to __terminate__). It is up to the environment to manage the permissions of this event.

    Attributes:
        kill (int, optional): The id of the agent to kill. Defaults the source of this event (if executed by an agent, the agent will kill itself).
    """

    kill: int = Field(default_factory=lambda: KillEvent._DEFAULT_UUID)

    @model_validator("kill", mode="after")
    def _validate_kill(self):
        if self.kill == KillEvent._DEFAULT_UUID:
            self.kill = self.source

    _DEFAULT_UUID: ClassVar[int] = int64_uuid()
