__all__ = ("UnknownEventType",)


class UnknownEventType(TypeError):
    """Exception raised when an unknown event type is encountered."""

    def __init__(self, event):
        event_type = type(event)
        super().__init__(f"Unknown event type: {event_type}.")
        self.event_type = event_type
