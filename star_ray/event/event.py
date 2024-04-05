""" Module defining the [Event] class."""

import time
from pydantic import BaseModel, Field, model_serializer
from ..utils import int64_uuid

EVENT_TIMESTAMP_FUNC = time.time
EVENT_UUID_FUNC = int64_uuid


class Event(BaseModel):
    """A simple event class with a unique identifier and a timestamp.

    Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int]): A unique identifier for the source of this event.
    """

    id: int = Field(default_factory=EVENT_UUID_FUNC)
    timestamp: float = Field(default_factory=EVENT_TIMESTAMP_FUNC)
    source: int

    # @model_serializer(mode="wrap")
    # def _serialize_model(self, handler):
    #     result = handler(self)
    #     result["event_type"] = self.__class__.__name__
    #     return result
