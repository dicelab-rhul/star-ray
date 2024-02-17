""" Module defining the [Event] class."""

import uuid
from dataclasses import dataclass
import time


@dataclass
class Event:
    """A simple event class with a unique identifier and a timestamp.

    Attributes:
        id ([str]): A unique identifier for the event, represented as a string.
        timestamp ([float]): The UNIX timestamp (in seconds) when the event instance is created.
        source ([str]): A unique identifier for the source of this event, represented as a string.
    """

    id: str
    timestamp: float
    source: str

    @staticmethod
    def new(source: str) -> "Event":
        """Creates a new instance of [Event] with a unique UUID as its id and a current UNIX timestamp.

        This method generates a UUID4, converts it to a string, and gets the current UNIX time (in seconds) to be used as the event's ID and timestamp respectively.
        Args:
            source ([str]): A unique identifier for the source of this event, represented as a string.
        Returns:
            Event: A new instance of the Event class with a unique ID and a timestamp.
        """
        return Event(id=Event.new_uuid(), timestamp=time.time(), source=source)

    @staticmethod
    def new_uuid() -> str:
        return str(uuid.uuid4())
