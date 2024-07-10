from typing import Callable, Any, Type, Dict, List
from collections import defaultdict
from functools import lru_cache, wraps
import inspect
import typing
import types


class _TypeRouter:

    def __init__(self, cache_size=1024):
        super().__init__()
        self._router = defaultdict(list)

        @lru_cache(maxsize=cache_size)
        def _get_funcs(t: Type):
            for t in t.mro():
                funcs = self._router.get(
                    _TypeRouter.fully_qualified_name(t), None)
                if funcs:
                    return funcs
            return self._router.get(_TypeRouter.fully_qualified_name(typing.Any), [])
        self._get_funcs = _get_funcs

    def add(self, func: Callable, route_types: List[Type] = None):
        if route_types is None:
            assert hasattr(func, "route_types")
            route_types = func.route_types
        else:
            route_types = _TypeRouter.resolve_route_types(route_types)

        for t in route_types:
            fqn = _TypeRouter.fully_qualified_name(t)
            self._router[fqn].append(func)
        # cache must be recomputed if we add a new type.
        self._get_funcs.cache_clear()

    def __call__(self, event: Any, *args, **kwargs) -> List[Any]:
        result = []
        for func in self._get_funcs(type(event)):
            result.append(func(event, *args, **kwargs))
        return result

    @staticmethod
    def fully_qualified_name(type):
        return type.__module__ + '.' + type.__name__

    @staticmethod
    def get_all_decorated_methods(obj: Any):
        methods = inspect.getmembers(obj, predicate=inspect.ismethod)
        methods = [m[1] for m in methods]
        return list(filter(lambda x: hasattr(x, "route_types"), methods))

    @staticmethod
    def resolve_route_types(_types: Type | List[Type]) -> List[Type]:
        if not isinstance(_types, (list, tuple)):
            _types = [_types]
        result = []
        for type in _types:
            origin = typing.get_origin(type)
            if origin is None:
                result.append(type)
            elif origin == types.UnionType or origin == typing.Union:
                result.extend(_TypeRouter.resolve_route_types(
                    typing.get_args(type)))
            else:
                result.append(origin)
        return result

    @staticmethod
    def route(*route_types: List[Type]):
        def _route(func, route_types=None):
            if route_types is None:
                route_types = resolve_first_argument_types(
                    func, allow_no_arguments=True)
            else:
                route_types = _TypeRouter.resolve_route_types(route_types)
            # this is used to automatically route events to a given component.
            if route_types:
                route_types = _validate_route_types(func, route_types)
                func.route_types = route_types
            return func

        if len(route_types) == 0:
            return _route
        elif len(route_types) == 1 and isinstance(route_types[0], (list, tuple)):
            def _wrap(func, route_types=route_types[0]):
                return _route(func, route_types=route_types)
            return _wrap
        elif len(route_types) == 1:
            # event_types is actually the function we are wrapping... used the decorator as @attempt without arguments
            return _route(route_types[0], route_types=None)
        else:
            raise ValueError(
                "Decorator `route` takes a single positional argument `route_types`.")


def attempt(*event_types: List[Type]):
    """A decorator that defines an `attempt` method within a `Component`. `attempt` methods should be called in the agent's `__cycle__` method to schedule an action for execution. This is true of both actuators and sensors.
    Sensors: `Sensor` actions will be attempted at the start of the next cycle (before the next `__cycle__` is called).
    Actuators: `Actuator` actions will be attempted at the end of the agents current cycle (after `__cycle__` has finished).

    Args:
        event_types (List[Type]): A list of types that the decorated `Component` method will receive if event routing is enabled. If this is not specified then an attempt will be made to discover the types via the type hint of the first argument. 

    Example:
    ```
    class MyActuator(Actuator):

        @attempt
        def move(self, direction):
            return MoveAction(direction)

    class MyAgent(Agent):
        def __cycle__(self):
            # the action will be executed after __cycle__ is finished.
            self.actuators[0].move("EAST")
    ```
    """

    def _attempt(func, route_types=None):
        if route_types is None:
            route_types = resolve_first_argument_types(
                func, allow_no_arguments=True)
        else:
            route_types = _TypeRouter.resolve_route_types(route_types)

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
        if route_types:
            route_types = _validate_route_types(func, route_types)
            wrapper.route_types = route_types
        return wrapper

    if len(event_types) == 0:
        return _attempt
    elif len(event_types) == 1 and isinstance(event_types[0], (list, tuple)):
        def _wrap(func, route_types=event_types[0]):
            return _attempt(func, route_types=route_types)
        return _wrap
    elif len(event_types) == 1:
        # event_types is actually the function we are wrapping... used the decorator as @attempt without arguments
        return _attempt(event_types[0], route_types=None)
    else:
        raise ValueError(
            "Decorator `attempt` takes a single positional argument `event_types`.")


def observe(*event_types: List[Type]):
    def _observe(func, route_types=None):
        if route_types is None:
            route_types = resolve_first_argument_types(
                func, allow_no_arguments=False)

        # used to identify whether a given method has been decorated with this decorator.
        func.is_observe = True
        # this is used to automatically route events to a given component.
        if route_types:
            route_types = _validate_route_types(func, route_types)
            func.route_types = route_types
        return func

    if len(event_types) == 0:
        return _observe
    elif len(event_types) == 1 and isinstance(event_types[0], (list, tuple)):
        def _wrap(func, route_types=event_types[0]):
            return _observe(func, route_types=route_types)
        return _wrap
    elif len(event_types) == 1:
        # event_types is actually the fun we are wrapping... used the decorator as @observe without arguments
        return _observe(event_types[0], route_types=None)
    else:
        raise ValueError(
            "Decorator `observe` takes a single positional argument `event_types`.")


def resolve_first_argument_types(func: Callable, allow_no_arguments=False):
    # attempt to resolve these by inspecting the func signature type hints
    parameters = list(inspect.signature(func).parameters.items())
    if len(parameters) == 0:
        if not allow_no_arguments:
            raise ValueError("Function has no arguments.")
        else:
            return None
    # TODO this is not very robust...
    if parameters[0][0] in ("self", "cls"):
        parameters = parameters[1:]
    if len(parameters) == 0:
        if not allow_no_arguments:
            raise ValueError("Function has no arguments.")
        else:
            return None
    first = parameters[0][1]
    return _TypeRouter.resolve_route_types([first.annotation])


def _validate_route_types(fun, route_types):
    def _get_message():
        return f"Decorator received invalid arguments for {fun}: %s"
    # validate the routes provided
    if not isinstance(route_types, (list, tuple)):
        raise ValueError(
            _get_message() % "`route_types` must be a list or tuple.")
    if len(route_types) == 0:
        raise ValueError(_get_message() %
                         "`route_types` must not be empty.")
    for cls in route_types:
        if not (isinstance(cls, (type, types.UnionType)) or cls is typing.Any):
            raise ValueError(
                _get_message() %
                f"`route_types` must contain only types but received {cls}",
            )
    return list(route_types)
