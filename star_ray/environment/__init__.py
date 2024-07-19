"""Package that defines environment related functionality.

Important classes:
    - `Environment`: the container and entry point of an agent simulation.
    - `Ambient`: defines the state of the environment and holds references to all agents in the simulation.
"""

from .environment import Environment
from .ambient import Ambient, _Ambient

State = _Ambient  # TODO temporary, we need to think more about how the environment state is going to be provided to agents

__all__ = ("Environment", "Ambient", "State")
