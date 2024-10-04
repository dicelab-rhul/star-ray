"""Module defines the `Agent` base class, which should be used for all agent implementations. It partially defines the agent-environment interaction API. See class documentation for details."""

from __future__ import annotations

from abc import abstractmethod, ABC
from .component import Sensor, Actuator, Component
from ..utils import int64_uuid

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ..environment import State


S = TypeVar("S", bound=Sensor)
A = TypeVar("A", bound=Actuator)


class Agent(ABC):
    """An agent is a small program that runs in a loop, continously sensing its environment and taking actions to modify it.

    The execution of the agent is typically managed by its environment and proceedes via the following method calls:
    - `__initialise__(state)` set up the agent.
    - <LOOP BEGINS>
    - `__sense__(state)` where sensing happens.
    - `__cycle__()` where  "thinking", learning and decision making happens.
    - `__execute__(state)` where acting happens.
    - <LOOP ENDS>
    - `__terminate__(state)` tear down the agent.

    These methods should never be called by the agent itself.

    In a typical implementation, a subclass of `Agent` will implement:
    - `__initialise__`
    - `__cycle__`
    - `__terminate__`

    The `__sense__` and `__execute__` methods will handle sensing and acting via the agents `Sensor`s and `Actuator`s automatically, but they may be overriden in some advanced cases.

    ### Thinking

    Thinking happens in `__cycle__`, this is where an agent will update its beliefs and make decisions.
    A typically `__cycle__` implementation may look as follows:
    ```
    def __cycle__(self):
        # process observations and update beliefs/learn
        for sensor in self.sensors:
            for observation in sensor.iter_observations():
                pass  # update beliefs
        for actuator in self.actuators:
            for observation in sensor.iter_observations():
                pass  # update beliefs (and typically handle any errors)

        # take actions based on beliefs
        if self.beliefs["empty_ahead"]:
            self.actuators[0].move_ahead()
        else:
            self.sensors[0].empty_ahead()
        # take other actions
    ```
    Note that both sensors and actuators can take actions, and recieve obervations (as a result of actions), see below.

    ### Sensing

    An `Agent` senses via its collection of `Sensor`s, each defines "read-only" actions which are taken during the call `__sense__` before `__cycle__` is called. Observations will be gathered as a result of any actions and will typically be avaliable via the `iter_observations` method in the `Sensor`.
    Some `Sensor`s may instead define convenience methods for the `Agent` to use which extract relevant information from the most recent observations.

    ### Acting

    An `Agent` acts via its collection of `Actuator`s, each defines "write" actions which are taken during the call to `__execute__` after `__cycle__` is called. In some cases, an `Actuator` may receive feedback from the envirronment in the form of an observation. `Actuator` observations will typically contain error messages or feedback about whether a given action was successful. Whether `Actuator`s receive any feedback at all is environment dependent. Note that the observations gathered from an `Actuator` (again via `iter_observations`) are from the PREVIOUS cycle, there will always be zero `Actuator` observations on the first call to `__cycle__`.

    See also: `AgentRouted`
    """

    def __init__(
        self, sensors: list[Sensor], actuators: list[Actuator], *args, **kwargs
    ):
        """Constructor.

        Args:
            sensors (List[Sensor]): collection of sensors.
            actuators (List[Actuator]): collection of actuators.
            args (tuple[Any], optional): optional additional arguments.
            kwargs (dict[str, Any], optional): optional additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._id = int64_uuid()
        self._sensors: set[Sensor] = set()
        self._actuators: set[Actuator] = set()

        self._ic: set[Component] = set()  # components to initialise
        self._tc: set[Component] = set()  # components to terminate

        self._is_initialised = False
        self._is_terminated = False

        for sensor in sensors:
            self.add_component(sensor)
        for actuator in actuators:
            self.add_component(actuator)

        if len(self.sensors) != len(sensors) or len(self.actuators) != len(actuators):
            raise ValueError(
                "Components were not added to this agent upon initialisation, did you override `add_component` and forget to call super()?"
            )

    @property
    def sensors(self) -> set[Sensor]:
        """Getter for the agent's `Sensor`s.

        Returns:
            Set[Sensor]: set of sensors.
        """
        return set(self._sensors)

    def get_sensors(self, oftype: type[S] | None = None) -> set[S]:
        """Getter for the agent's `Sensor`s.

        Arguments:
            oftype (type): type sensor(s) to get.

        Returns:
            Set[Sensor]: set of sensors.
        """
        if oftype:
            return set(filter(lambda x: isinstance(x, oftype), self._sensors))
        else:
            return set(self._sensors)

    @property
    def actuators(self) -> set[Actuator]:
        """Getter for the agent's `Actuator`s.

        Returns:
            Set[Sensor]: set of actuators.
        """
        return set(self._actuators)

    def get_actuators(self, oftype: type[A] | None = None) -> set[A]:
        """Getter for the agent's `Actuator`s.

        Arguments:
            oftype (type): type sensor(s) to get.

        Returns:
            Set[Actuator]: set of actuators.
        """
        if oftype:
            return set(filter(lambda x: isinstance(x, oftype), self._actuators))
        else:
            return set(self._actuators)

    @property
    def id(self) -> int:
        """Getter for the agent's unique id (read-only).

        Returns:
           int: the agent's id.
        """
        return self._id

    def get_id(self) -> int:
        """Getter for the agent's unique id (read-only).

        Returns:
           int: the agent's id.
        """
        return self._id

    def __initialise__(self, state: State):
        """Initialises the agent. Overriding allows set up of the agent. Initial sense actions may be triggered here to ensure the resulting observations are avaliable in the first call to `__cycle__`.

        Args:
            state (State): the state of the environment.
        """
        # TODO call query?

    def __terminate__(self, state: State):
        """Terminates the agent. Overriding allows safe clean up of any resources the agent or its `Component`s might be using. By default this will automatically remove all sensors and actuators from the agent to allow them to perform safe clean up.

        Args:
            state (State): the state of the environment.
        """
        for sensor in self.sensors:
            self.remove_component(sensor)
        for actuator in self.actuators:
            self.remove_component(actuator)
        # TODO call query?

    def __sense__(self, state: State, *args, **kwargs):
        """Take sense actions via the agents sensors. This should never be called from within the `Agent`.

        Args:
            state (State): the state of the environment.
            args (tuple[Any], optional): optional additional arguments.
            kwargs (dict[str, Any], optional): optional additional keyword arguments.
        """
        _ = [sensor.__query__(state) for sensor in self.sensors]

    @abstractmethod
    def __cycle__(self):
        """Update beliefs/learn and take actions via sensors and actuators."""

    def __execute__(self, state: State, *args, **kwargs):
        """Executes actions via the agents actuators. This should never be called from within the `Agent`.

        Args:
            state (State): the state of the environment.
            args (tuple[Any], optional): optional additional arguments.
            kwargs (dict[str, Any], optional): optional additional keyword arguments.
        """
        _ = [actuator.__query__(state) for actuator in self.actuators]

    def add_component(self, component: Component) -> Component:
        """Add a new component (sensor or actuator) to this agent.

        Args:
            component (Component): the component to add.

        Raises:
            TypeError: if the component is not of type `Sensor` or `Actuator`.

        Returns:
            Component: the component added.
        """
        if isinstance(component, Sensor):
            self._sensors.add(component)
        elif isinstance(component, Actuator):
            self._actuators.add(component)
        else:
            raise TypeError(f"Unsupported component type: {type(component)}")
        component.on_add(self)
        return component

    def remove_component(self, component: Component) -> Component:
        """Removes an existing component from this agent.

        Args:
            component (Component): component to remove.

        Raises:
            TypeError: if the component is not of type `Sensor` or `Actuator`.

        Returns:
            Component: the component that was removed.
        """
        if isinstance(component, Sensor):
            self._sensors.remove(component)
        elif isinstance(component, Actuator):
            self._actuators.remove(component)
        else:
            raise TypeError(f"Unsupported component type: {type(component)}")
        component.on_remove(self)
        return component
