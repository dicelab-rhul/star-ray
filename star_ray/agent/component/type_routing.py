from typing import Callable, Any, Type, Dict, List
from collections import defaultdict
from functools import lru_cache
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
            return []
        self._get_funcs = _get_funcs

    def add(self, func: Callable):
        assert hasattr(func, "route_types")
        for t in func.route_types:
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


def observe(*event_types: List[Type]):
    def _observe(func, route_types=None):
        if route_types is None:
            # attempt to resolve these by inspecting the func signature type hints
            parameters = list(inspect.signature(func).parameters.items())
            # TODO this is not very robust...
            first = parameters[1][1] if parameters[0][0] in (
                "self", "cls") else parameters[0][1]
            origin = typing.get_origin(first.annotation)
            if origin == types.UnionType:
                route_types = list(typing.get_args(first.annotation))
            elif origin:
                route_types = [origin]
            else:
                route_types = [first]
        # used to identify whether a given method has been decorated with this decorator.
        func.is_observe = True
        # this is used to automatically route events to a given component.
        if not route_types is None:
            route_types = _validate_route_types(func, route_types)
        func.route_types = route_types
        return func

    if len(event_types) == 0:
        return _observe
    elif len(event_types) == 1 and isinstance(event_types, (list, tuple)):
        def _wrap(func, route_types=event_types[0]):
            return _observe(func, route_types=route_types)
        return _wrap
    elif len(event_types) == 1:
        # event_type is actually the fun we are wrapping... used the decorator as @observe without arguments
        return _observe(event_types[0], route_types=None)
    else:
        raise ValueError(
            "Decorator @observe takes a single positional argument `event_types`.")


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
        if not isinstance(cls, type):
            raise ValueError(
                _get_message() %
                f"`route_types` must contain only types but received {cls}",
            )
    return list(route_types)
