""" Module defining the [ExitEvent] class. [ExitEvent] is used to signal that the program should close."""

from dataclasses import dataclass
from .event import Event


@dataclass
class ExitEvent(Event):
    """An event class representing a program exit event.

    Attributes:
        id ([str]): A unique identifier for the event, represented as a string (inherited).
        timestamp ([float]): The UNIX timestamp (in seconds) when the event instance is created (inherited).
        source ([str]): A unique identifier for the source of this event, represented as a string (inherited).

    """
