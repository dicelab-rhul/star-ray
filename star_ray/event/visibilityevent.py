""" Module defining the [VisibilityEvent] class. """

from typing import ClassVar
from dataclasses import dataclass, astuple
from .event import Event


@dataclass
class VisibilityEvent(Event):
    """
    A class representing a visibility change event. If this event is triggered it is an indicator that the user has either:
        1. switch window (changed focus)
        2. switched tab (if using a browser based UI)
        3. minimised the UI window

    This event DOES NOT indicate that the use cannot see the interface at all, this is due to inherent limitations with detecting visibility changes (e.g. in browser based UI's). See e.g. [visibilitychange](https://developer.mozilla.org/en-US/docs/Web/API/Document/visibilitychange_event)

    Attributes:
        id (str): A unique identifier for the event, represented as a string (inherited).
        timestamp (float): The UNIX timestamp (in seconds) when the event instance is created (inherited).
        source ([str]): A unique identifier for the source of this event, represented as a string (inherited).
        status ([int]): the visibility status (VISIBLE = 0, HIDDEN = 1).
    """

    status: int

    # static fields
    VISIBLE: ClassVar[int] = 0
    HIDDEN: ClassVar[int] = 1

    @staticmethod
    def new(source: str, visibility: int) -> "VisibilityEvent":
        return VisibilityEvent(*astuple(Event.new(source)), visibility)

    @staticmethod
    def new_visible(source: str) -> "VisibilityEvent":
        return VisibilityEvent(*astuple(Event.new(source)), VisibilityEvent.VISIBLE)

    @staticmethod
    def new_hidden(source: str) -> "VisibilityEvent":
        return VisibilityEvent(*astuple(Event.new(source)), VisibilityEvent.HIDDEN)
