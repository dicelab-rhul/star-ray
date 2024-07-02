from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import List, Any, TYPE_CHECKING
from functools import wraps

from ...event import Observation, Action
from ..wrapper_observations import _Observations
from ...utils import int64_uuid

if TYPE_CHECKING:
    from ..agent import Agent
    from ...environment.wrapper_state import State


__all__ = (
    "ComponentMeta",
    "Component",
    "attempt",
)

ATTEMPT_METHOD_CLS_VAR = "__attemptmethods__"
IS_ATTEMPT_VAR = "is_attempt"


def _is_attempt_method(obj):
    return callable(obj) and hasattr(obj, IS_ATTEMPT_VAR)
    # return inspect.ismethod(obj) and hasattr(obj, IS_ATTEMPT_VAR)


class _ComponentMeta(type):
    def __new__(cls, name, bases, dct):
        # Get all methods decorated with the attempt_decorator
        attempt_methods = [attr for _, attr in dct.items() if _is_attempt_method(attr)]
        # get attempt methods in base classes, these should not change...
        for base in bases:
            attempt_methods.extend(getattr(base, ATTEMPT_METHOD_CLS_VAR, []))
        dct[ATTEMPT_METHOD_CLS_VAR] = attempt_methods
        return super().__new__(cls, name, bases, dct)


class ComponentMeta(ABCMeta, _ComponentMeta):
    pass


class Component(metaclass=ComponentMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id: int = int64_uuid()
        # this will be set by the agent when this component is added to it.
        # generally it should not be accessed unless you know what you are doing!
        self._agent = None

        # actions to attempt in the current cycle to produce observations
        self._actions: List[Action] = []  # TODO allow async access here?
        # observations that result from taking action
        self._observations: _Observations = _Observations.empty()

    def on_add(self, agent: Agent) -> None:
        self._agent = agent

    def on_remove(self, agent: Agent) -> None:
        self._agent = None

    def __str__(self):
        return f"{self.__class__.__name__}({self._id})"

    def __repr__(self):
        # TODO perhaps include information about the agent this component is attached to ?
        return str(self)

    @property
    def id(self):
        """Unique identifier for this [`Component`].

        Returns:
            (`str`): unique identifier
        """
        return self._id

    def iter_observations(self):
        yield from filter(None, self._observations)

    def iter_actions(self):
        yield from filter(None, self._actions)

    async def aiter_observations(self):
        raise NotImplementedError("TODO")

    async def aiter_actions(self):
        raise NotImplementedError("TODO")

    def __transduce__(self, events: List[Observation]) -> List[Observation]:
        return events

    def __initialise__(self, state: State) -> None:
        """Method called when the enviroment is read, this can be used to set up the component.
        For example, a sensor might subscribe to receive certain events here.

        Args:
            state (State): state of the environment
        """

    @abstractmethod
    def __query__(self, state: State) -> None:
        """Calling this method will cause this [`Component`] to query the state of the environment.
        This should not be called manually, it will be called by the environment execution scheduler.
        """

    def _set_source(self, actions):
        for action in actions:
            # TODO or perhaps we should use the id of the agent?
            if action.source is None:
                action.source = self.id


def attempt(*fun, route_events=None):
    """A decorator that defines an `attempt` method within a [Component]. `attempt` methods should be called in the agent's `__cycle__` method to schedule an action for execution. This is true of both actuators and sensors.
    Sensors:
        Any [`Sensor`] actions will be attempted at the start of the next cycle (before the next `__cycle__` is called).
        TODO [PassiveSensor]

    Actuators:
        Any [`Actuator`] actions will be attempted at the end of the agents current cycle (after `__cycle__` has finished).
        TODO [PassiveActuator]

    Args:
        fun ([`Callable`]): a function to wrap.

    Example:
    ```
    class MyActuator(Actuator):

        @Actuator.attempt
        def move(self, direction):
            return MoveAction(direction)

    class MyAgent(Agent):
        def __cycle__(self):
            # the action will be executed after __cycle__ is finished.
            self.actuators[0].move("EAST")
    ```
    """

    def _attempt(func, route_events=route_events):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            action = func(self, *args, **kwargs)
            if isinstance(action, (list, tuple)):
                self._actions.extend(action)  # pylint: disable=W0212
            else:
                self._actions.append(action)  # pylint: disable=W0212
            return action

        # used to identify whether a given method has been decorated with this decorator.
        wrapper.is_attempt = True
        # this is used to automatically route events to a given component.
        if not route_events is None:
            route_events = _validate_route_events(fun, route_events)
        wrapper.route_events = route_events
        return wrapper

    if len(fun) == 0:
        return _attempt
    elif len(fun) == 1:
        return _attempt(fun[0])
    else:
        raise ValueError(
            f"Invalid arguments: {fun}, should contain only function to decorate, use keyword arguments otherwise."
        )


def _validate_route_events(fun, route_events):
    def _get_message():
        return f"`attempt` decorator received invalid arguments for fun {fun}:"

    # validate the routes provided
    if not isinstance(route_events, (list, tuple)):
        raise ValueError(_get_message(), "`route_events` must be a list or tuple.")
    if len(route_events) == 0:
        raise ValueError(_get_message(), "`route_events` must not be empty.")
    for cls in route_events:
        if not isinstance(cls, type):
            raise ValueError(
                _get_message(),
                f"`route_events` must contain only types but received {cls}",
            )
    return list(route_events)
