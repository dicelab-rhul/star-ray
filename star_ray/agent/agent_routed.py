"""Module defines the `AgentRouted` class and the `observe` and `decide` decorators. See class documentation for details."""

from typing import Any
from collections.abc import Callable
from functools import wraps
import inspect

from .component import Component
from .component import Sensor, Actuator
from .agent import Agent

from ..utils import TypeRouter
from ..event import Event

__all__ = ("AgentRouted", "observe", "decide")


def _get_decide_methods(obj: Any) -> list[Callable]:
    """Internal method that will retreive all (bound) methods on `obj` that have been tagged with `is_decide`. This tag is added if the method has been decorted with `@decide`.

    Args:
        obj (Any): object to get decide methods from.

    """
    methods = inspect.getmembers(obj, predicate=inspect.ismethod)
    return [m[1] for m in filter(lambda x: getattr(x[1], "is_decide", False), methods)]


def _component_arg(func: Callable) -> Callable:
    """Internal decorate that is used to resolve the optional `component` argument in a method decorated with `@observe`. Observe methods are not required to define the `component` argument, but if it is define the sensor or actuator will be provided.

    Args:
        func (Callable): the method

    Returns:
        Callable: the wrapped method that handles `component` if required, otherwise the original `func` argument.
    """
    kwargs = list(inspect.signature(func).parameters.keys())
    if "component" in kwargs:
        return func
    else:

        @wraps(func)
        def _wrapped(*args, **kwargs):
            del kwargs["component"]
            return func(*args, **kwargs)

        return _wrapped


def decide(*fun: Callable):
    """A decorator that may be added to methods in a `RoutedAgent` that are intended to produce actions for execution (i.e. the decision of the agent). These actions will be automatically routed to components that define type-compatible attempt methods.

    Example:
    ```
    class MyAgent(RoutedAgent):
        @decide
        def my_decide(self) -> Event:
            return MyDecision()  # send to relevant actuators during `__cycle__`


    class MyActuator(Actuator):
        @attempt
        def my_attempt(self, decision: MyDecision) -> MyAction:
            return MyAction()  # the action is now scheduled for execution
    ```

    Note that if multiple compatible components are discovered then all of them will receive the decision/action. Some care may be need to avoid duplicate execution if the decision is an executable action.

    As a principle, attempt methods should always be conservative with their typing if used in routing. There are very few situations where multiple components should define attempt methods that have very generic typings (e.g. `Event` or `Action`) as this can easily lead to duplicate actions being executed, see `@attempt` for further details.
    """

    def _decide(f):
        f.is_decide = True
        return f

    if len(fun) == 0:
        return _decide
    elif len(fun) == 1:
        return _decide(fun[0])
    else:
        raise ValueError("`decide` decorator takes no arguments.")


def observe(*event_types: tuple[type]):
    """A decorator that may be added to methods in `AgentRouted` that are intended to process observations. Such methods will automatically receive type-compatible observations from the agents components (sensors and actuators).

    Args:
        event_types (tuple[type], optional): the types to receive, a single positional argument may be provide i.e. @observe([A,B,C]), if not argument is provided i.e. usage `@observe` or `@observe()` then types will be derived from the type hint of the first argument of the decorated method.

    Example:
    ```
    class MyAgent(RoutedAgent):
        @observe
        def revise_beliefs(self, observation: MyObservation, component: Component):
            # `component` is sensor or actuator that produced the observation, it is optional
            pass  # revise agents beliefs
    ```

    The `component` argument in an observe method is optional a valid signature would also be: `revise_beliefs(self, observation : MyObservation)`

    Raises:
        ValueError: if `event_types` is not specified correctly or multiple positional arguments are provided.
    """

    def _observe(func, route_types=None):
        if route_types is None:
            route_types = TypeRouter.resolve_first_argument_types(
                func, allow_no_arguments=False
            )

        # used to identify whether a given method has been decorated with this decorator.
        func.is_observe = True
        # this is used to automatically route events to a given component.
        if route_types:
            route_types = TypeRouter.validate_types(route_types)
            func.route_types = route_types
        return func

    if len(event_types) == 0:
        return _observe
    elif len(event_types) == 1 and isinstance(event_types[0], list | tuple):

        def _wrap(func, route_types=event_types[0]):
            return _observe(func, route_types=route_types)

        return _wrap
    elif len(event_types) == 1:
        # event_types is actually the fun we are wrapping... used the decorator as @observe without arguments
        return _observe(event_types[0], route_types=None)
    else:
        raise ValueError(
            "Decorator `observe` takes a single positional argument `event_types`."
        )


class AgentRouted(Agent):
    """An agent base class adds automatic routing of observation/decision/actions to relevant methods, sensors and actuators by type. The `__cycle__` method has been defined to handle this.

    # Observe, Decide, Attempt

    Three decorators are used to enable this routing.

    - `observe`: used to route observations from sensors to methods in the agent.
    - `decide` : used to route decisions (or actions) from the agent to type-compatible actuators (specifically their `attempt` methods).
    - `attempt` : used in actuators and sensors as a destination for routed decisions/actions (originating in decide methods).

    `observe` and `decide` are used to decorate methods in the agent.
    `attempt` is used to decorate methods in the agents components (sensors and actuators), recall that it is also used to schedule action for execution during `__sense__` (for sensors) and `__execute__` (for actuators).

    Methods decorated with any of the three are called during `__cycle__`.

    Example:
    ```
    class MyAgent(RoutedAgent):
        @observe
        def my_revise(self, observation: MyObservation, component: Component):
            pass  # observations of type `MyObservation` will be sent here from sensors (or actuators)

        @decide
        def my_decide(self) -> MyDecision:
            return MyDecision()  # send to the type-compatible actuator

        @decide
        def my_sense(self) -> MySense:
            return MySense()  # send to the type-compatible sensor


    class MyActuator(Actuator):
        @attempt
        def my_attempt(self, decision: MyDecision) -> MyAction:
            return MyAction()


    class MySensor(Actuator):
        @attempt
        def my_attempt(self, decision: MySense) -> MyAction:
            return MySenseAction()
    ```
    For more details on each decorator, see their respective documentation.

    Methods that have been decorated with `observe` and `decide` are automatically discovered, but it is also possible to manually add functions via the `add_observe` and `add_decide` methods. The added function does not need to be an instance method.

    During `__cycle__` the following methods dunder methods are called: `__observe__`, `__decide__`.

    - `__observe__` is responsible for routing observations from sensors to type-compatible observe methods.
    - `__decide__` is responsible for routing decisions (or actions) from decide methods to type-compatible actuators (attempt methods).
    """

    _TYPE_ROUTER_CACHE_SIZE = 64  # default value for router cache size

    def __init__(
        self, sensors: list[Sensor], actuators: list[Actuator], *args, **kwargs
    ):
        """Constructor.

        Args:
            sensors (list[Sensor]): initial sensor components.
            actuators (list[Actuator]): initial actuator components.
            args (tuple[Any], optional): optional additional arguments.
            kwargs (dict[str, Any], optional): optional additional keyword arguments.
        """
        # this may be added to in super().__init__ (upon adding an actuator)
        # it will route actions to the type-compatible component attempt methods
        self._attempt_routers: dict[int, TypeRouter] = dict()

        super().__init__(sensors, actuators, *args, **kwargs)
        # router for observations to type-compatible observe methods
        self._observe_router = TypeRouter(
            cache_size=AgentRouted._TYPE_ROUTER_CACHE_SIZE
        )
        # these methods are those that have been decorated with @observe
        # they will recieve observations of the relevant type from the sensors.
        self._observe_methods = list(
            filter(
                lambda m: getattr(m, "is_observe", False),
                TypeRouter.get_all_decorated_methods(self),
            )
        )
        for method in self._observe_methods:
            self._observe_router.add(_component_arg(method))

        # these methods are those that have been decorated with @decide, they are to be called in `__cycle__`.
        self._decide_methods = _get_decide_methods(self)

    def add_observe(self, func: Callable, event_types: list[type[Event]] | None = None):
        """Adds a new observe function. The function need not be decorated with `@observe`.

        Args:
            func (Callable): function to add.
            event_types (list[type], optional): `event_types` to route to the function. Defaults to None. If not specified the types will be resolved from the type hints of the first argument of `func` argument (unless the @observe decorator was used).
        """
        func = _component_arg(func)  # handle optional "component" argument
        self._observe_methods.append(func)
        self._observe_router.add(func, event_types)

    def add_decide(self, func: Callable):
        """Adds a new decide function. The function need not be decorated with `@decide`.

        Args:
            func (Callable): function to add.
        """
        if not hasattr(func, "is_decide"):
            func = decide(func)
        self._decide_methods(func)

    def attempt(self, action: Event | list[Event], component: Component | None = None):
        """Manually attempt one or more actions and route to the provide component.

        If `component` is not provided, this method will search for the relevant component(s) to attempt the `action` based on its type using the usual action/decision routing mechanism.

        Args:
            action (Event | List[Event]): action (or actions) to attempt.
            component (Component, optional): to attempt with. Defaults to None.
        """
        if not isinstance(action, list | tuple):
            action = (action,)
        if component is None:
            for attempt_router in self._attempt_routers.values():
                for a in filter(None, action):
                    attempt_router(a)
        else:
            attempt_router = self._attempt_routers[component.id]
            for a in filter(None, action):
                attempt_router(a)

    def add_component(self, component: Component) -> Component:  # noqa
        component = super().add_component(component)
        # get attempt methods from the component (if any) and register them with a new TypeRouter
        attempt_methods = list(
            filter(
                lambda m: getattr(m, "is_attempt", False),
                TypeRouter.get_all_decorated_methods(component),
            )
        )
        if len(attempt_methods) > 0:
            attempt_router = TypeRouter(cache_size=AgentRouted._TYPE_ROUTER_CACHE_SIZE)
            for method in attempt_methods:
                attempt_router.add(method)
            self._attempt_routers[component.id] = attempt_router
        else:
            pass  # no attempt methods were defined
        return component

    def remove_component(self, component: Component) -> Component:  # noqa
        component = super().remove_component(component)
        if component.id in self._attempt_routers:
            del self._attempt_routers[component.id]
        return component

    def __cycle__(self):  # noqa
        self.__observe__()
        self.__decide__()

    def __decide__(self) -> None:
        """Method that routes decisions/actions to type-compatible component attempt methods. Called once per cycle."""
        resulting_actions = []
        for method in self._decide_methods:
            # the method is already bound
            decisions = method()
            if not isinstance(decisions, list | tuple):
                decisions = [decisions]
            # forward the actions to the relevant actuators
            for decision in filter(None, decisions):
                for attempt_router in self._attempt_routers.values():
                    action = attempt_router(decision)
                    resulting_actions.append(action)
        return resulting_actions  # TODO do something with these?

    def __observe__(self):
        """Method that routes observations from components to type-compatible observe methods. Called once per cycle."""
        for actuator in self.get_actuators():
            for observation in actuator.iter_observations():
                assert isinstance(observation, Event)
                self._observe_router(observation, component=actuator)
        for sensor in self.get_sensors():
            for observation in sensor.iter_observations():
                assert isinstance(observation, Event)
                self._observe_router(observation, component=sensor)
