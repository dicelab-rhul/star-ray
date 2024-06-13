from pydantic import validator, Field

from .event import Event


# TODO untested...
class KillEvent(Event):
    """
        Event that will kill an agent given its id (trigger a call to __terminate__). It is up to the environment to manage the permission of use of this event.


    Attributes:
        kill (int, optional): The id of the agent to kill. Defaults the source of this event (if executed by an agent, the agent will kill itself).
    """

    kill: int = Field(default=None)

    @validator("kill", pre=True, always=True)
    def _validate_kill(cls, value, values):  # pylint: disable=E0213
        if value is None:
            return values.get("source")
        elif isinstance(value, int):
            return value
        else:
            raise ValueError(f"Invalid action_id {value}")
