""" Module defining the [Event] class."""

import time
from pydantic import BaseModel, Field
from ..utils import int64_uuid

EVENT_TIMESTAMP_FUNC = time.time
EVENT_UUID_FUNC = int64_uuid


class Event(BaseModel):
    """An event class with a unique identifier and a timestamp.

    Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int | None]): A unique identifier for the source of this event. By default this
    """

    id: int = Field(default_factory=EVENT_UUID_FUNC)
    timestamp: float = Field(default_factory=EVENT_TIMESTAMP_FUNC)
    source: int | None = Field(default_factory=lambda: None)

    class Config:
        validate_assignment = True
