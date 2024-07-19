"""Module defining the `TypeRouter` class. The class is used to route objects to type-compatible functions. See the class documentation for details."""

from typing import Any
from collections.abc import Callable
from collections import defaultdict
from functools import lru_cache
import inspect
import typing
import types as _types


class TypeRouter:
    """Route objects to type-compatible functions."""

    def __init__(self, cache_size: int = 1024):
        """Constructor.

        Args:
            cache_size (int, optional): the size of type mapping cache used to determine which functions should be called for a given input type (see `__call__`). Defaults to 1024.
        """
        super().__init__()
        self._router = defaultdict(list)

        @lru_cache(maxsize=cache_size)
        def _get_funcs(t: type):
            for t in t.mro():
                funcs = self._router.get(TypeRouter.fully_qualified_name(t), None)
                if funcs:
                    return funcs
            return self._router.get(TypeRouter.fully_qualified_name(typing.Any), [])

        self._get_funcs = _get_funcs

    def add(self, func: Callable, route_types: list[type] | None = None):
        """Add a new function that will be called if an instance with a type that inherits from any type in `route_types` is provided in `__call__`.

        Note: adding a new function will invalidate the type routing cache. This class is intended to be used statically (or new functions are to be added infreqently).

        Args:
            func (Callable): function to call.
            route_types (list[type] | None, optional): instance types to route. Defaults to None, in which case the types will be resolved from the type hints of the first argument of `func`.
        """
        if route_types is None:
            assert hasattr(func, "route_types")
            route_types = func.route_types
        else:
            route_types = TypeRouter.resolve_route_types(route_types)
        if route_types is None:
            raise ValueError(f"Failed to resolve `route_types` for function: {func}.")

        for t in route_types:
            fqn = TypeRouter.fully_qualified_name(t)
            self._router[fqn].append(func)
        # cache must be recomputed if we add a new type
        self._get_funcs.cache_clear()

    def __call__(self, event: Any, *args, **kwargs) -> list[Any]:
        """Routes the given `event` to type-compatible functions. If there is not exact type match, the called function is resvolved via the instance types method resolution order (mro). The function(s) that are assocaited with the inherited type that is highest in this hierarchy (i.e. the closest parent type) are called.

        Args:
            event (Any): to route, this will be provided as the first (positional) argument to the function(s).
            *args (Any, optional): additional arguments to provide to the function(s)
            **kwargs (Any, optional): additional keyword arguments to provide to the function(s)

        Returns:
            list[Any]: results of each function call (may be empty if no type-compatible functions were found).
        """
        result = []
        for func in self._get_funcs(type(event)):
            result.append(func(event, *args, **kwargs))
        return result

    @staticmethod
    def fully_qualified_name(type: type) -> str:
        """Get the fully qualified type name of the given type.

        Note that in this class types that have the same fully qualified name as assumed to be equal.

        Args:
            type (type): type to get name of

        Returns:
            str: fully qualified name of the type
        """
        return type.__module__ + "." + type.__name__

    @staticmethod
    def get_all_decorated_methods(obj: Any) -> list[Callable]:
        """Get all of the (bound) methods in the given object that have the `route_types` attribute.

        Args:
            obj (Any): object for which to get (bound) methods.

        Returns:
            list[Callable]: list of methods that have the `route_type` attribute.
        """
        methods = inspect.getmembers(obj, predicate=inspect.ismethod)
        methods = [m[1] for m in methods]
        return list(filter(lambda x: hasattr(x, "route_types"), methods))

    @staticmethod
    def resolve_route_types(types: type | list[type]) -> list[type]:
        """Resolve types from a list of types. This handles type hints and converts them into standard python types (i.e. python primitive types or class objects). It splits the `UnionType` into its consituent.

        Args:
            types (type | list[type]): types to resolve.

        Returns:
            list[type]: resolved types.
        """
        if not isinstance(types, list | tuple):
            types = [types]
        result = []
        for type in types:
            origin = typing.get_origin(type)
            if origin is None:
                result.append(type)
            elif origin == _types.UnionType or origin == typing.Union:
                result.extend(TypeRouter.resolve_route_types(typing.get_args(type)))
            else:
                result.append(origin)
        return result

    @staticmethod
    def route(*route_types: list[type]) -> Callable:
        """A decorator that will set up a function or method for use with the `TypeRouter` class, types will be resolved statically. This is intended to be used with `get_all_decorated_methods` which will discover all (bound) instance methods. The methods can then be added to an instance of `TypeRouter`.

        Args:
            route_types (list[type]): an optional list of types that will be used as the `route_types` for the given function. If this is not specified the types will be resolved from the first argument of the function (ignoring bound arguments `self` and `cls`).

        Example 1:
        ```
        class MyClass:
            @TypeRouter.route
            def foo(self, data: str | int):
                pass  # do something
        ```

        Example 2:
        ```
        class MyClass:
            @TypeRouter.route([int | str])
            def foo(self, data):
                pass  # do something
        ```

        Example 2:
        ```
        class MyClass:
            @TypeRouter.route([int, str])
            def foo(self, data):
                pass  # do something
        ```

        Note that if `route_types` is specified, this will be prefered over any type hints.
        """

        def _route(func, route_types=None):
            if route_types is None:
                route_types = TypeRouter.resolve_first_argument_types(
                    func, allow_no_arguments=True
                )
            else:
                route_types = TypeRouter.resolve_route_types(route_types)
            # this is used to automatically route events to a given component.
            if route_types:
                route_types = TypeRouter.validate_route_types(func, route_types)
                func.route_types = route_types
            return func

        if len(route_types) == 0:
            return _route
        elif len(route_types) == 1 and isinstance(route_types[0], list | tuple):

            def _wrap(func, route_types=route_types[0]):
                return _route(func, route_types=route_types)

            return _wrap
        elif len(route_types) == 1:
            # event_types is actually the function we are wrapping... used the decorator as @attempt without arguments
            return _route(route_types[0], route_types=None)
        else:
            raise ValueError(
                "Decorator `route` takes a single positional argument `route_types`."
            )

    @staticmethod
    def resolve_first_argument_types(
        func: Callable, allow_no_arguments=False
    ) -> list[type] | None:
        """Resolves the type(s) of the first argument of the given `func` from its type hints (ignoring bound arguments `self` or `cls`).

        Args:
            func (Callable): the function whose argument should be resolved
            allow_no_arguments (bool, optional): allow no arguments in the functions, if True always return None. Defaults to False.

        Raises:
            ValueError: if the function has no arguments and `allow_no_arguments=False`
            TypeError: if no type hint was defined for the first argument.

        Returns:
            list[type]: types of the first argument
        """
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
        if first.annotation == inspect._empty:
            raise TypeError(
                f"A type hint was not defined for first parameter of: {func}"
            )
        return TypeRouter.resolve_route_types([first.annotation])

    @staticmethod
    def validate_route_types(func: Callable, route_types: list[type]) -> list[type]:
        """Validate the `route_types` of a function. This is a utility method used typically used to validate the arguments provided to a TypeRouter.

        Args:
            func (Callable): the function that is being used, `route_types` may be derived from the type hints of this function, or may have been provided manually with the intention of later calling `func` with instances of these types.
            route_types (list[type]): types to validate.

        Raises:
            TypeError: if the types are not validate

        Returns:
            list[type]: the validated types (same as `route_types`)
        """
        try:
            return TypeRouter.validate_types(route_types)
        except Exception as e:
            raise TypeError(f"Invalid `route_types` for function: {func}") from e

    @staticmethod
    def validate_types(types: list[type]) -> list[type]:
        """Validate the types in `types`.

        Args:
            types (list[type]): to validate
        """
        # validate the routes provided
        if not isinstance(types, list | tuple):
            raise ValueError("types must be a list or tuple.")
        if len(types) == 0:
            raise ValueError("types must not be empty.")
        for cls in types:
            if not (isinstance(cls, type | _types.UnionType) or cls is typing.Any):
                raise ValueError(
                    f"types must contain only `type` but received: {cls}",
                )
        return list(types)
