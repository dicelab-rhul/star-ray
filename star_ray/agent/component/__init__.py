"""Package that defines component related functionality.

`Component`s can be attached to agents allowing them to perform certain actions and receive observations. They are in essence how the agent interfaces, or "interacts" with its enviroment.

Two important base classes:
    `Sensor` : TODO
    `Actuator` : TODO

This module also defines important decorators that may be used by an `Agent` to route actions/observations to methods that it defines. This can simplify how actions/observations are taken and processed during the agent's cycle.

- `@observe` : TODO
- `@decide` : TODO
- `@attempt` : TODO

See associated documentation for further details.

"""

from .component import Component
from .actuator import Actuator
from .attempt import attempt
from .on_awake import OnAwake
from .sensor import Sensor
from .sensor_io import IOSensor

__all__ = (
    "OnAwake",
    "attempt",
    "observe",
    "Component",
    "Sensor",
    "Actuator",
    "IOSensor",
)
