""" Module defining the [ExitEvent] class. [ExitEvent] is used to signal that the ui (or program) should close."""

from ..event import Event


class ExitEvent(Event):
    """An event class representing a ui exit.

    Attributes:
        id ([int]): A unique identifier for the event.
        timestamp ([float]): The timestamp (in seconds since UNIX epoch) when the event instance is created.
        source ([int]): A unique identifier for the source of this event.

    """
