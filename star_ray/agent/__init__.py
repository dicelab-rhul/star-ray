"""Package that defines agent related functionality.

Important classes:
    - `Agent` : the base class for an agent.
    - `Component` : the base class for a component (see `Actuator` and `Sensor`).
    - `Actuator` : A component that allows the agent to take actions in its environment.
    - `Sensor` : A component that allows an agent to observe its environment.

Other useful classes:
    - `AgentRouted` : An implementation of `Agent` that automatically routes actions/observations to assocaited actuators/sensors (based on types).

See respecitve class documentation for details.
"""

from ._wrapper_agent import _Agent
from ._wrapper_observations import _Observations

from .agent import Agent
from .agent_routed import AgentRouted, decide, observe

from .component import (
    attempt,
    Component,
    Sensor,
    Actuator,
    IOSensor,
)

__all__ = (
    "_Agent",
    "_Observations",
    "Agent",
    "AgentRouted",
    "decide",
    "attempt",
    "observe",
    "Component",
    "Sensor",
    "IOSensor",
    "Actuator",
)
