"""Module defining common exception types."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..event import Event

__all__ = ("UnknownEventType",)


class UnknownEventType(TypeError):
    """Exception raised when an unknown event type is encountered."""

    def __init__(self, event: Event):
        """Constructor.

        Args:
            event (_type_): _description_
        """
        event_type = type(event)
        super().__init__(f"Unknown event type: {event_type}.")
        self.event_type = event_type
