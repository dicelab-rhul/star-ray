# pylint: disable=W0212
from typing import Callable, List
import inspect


def change_listener(cls):
    """
    A class decorator that injects change listener functionality into a class.

    This decorator adds methods for adding, removing, and retrieving change listeners, and wraps the class's `__update__` method to automatically notify listeners about changes. It is intended for use with classes that have an `__update__` method modifying an XML state, requiring listeners to be notified on changes.

    After applying this decorator, the decorated class will have the following new methods and capabilities:

    - `add_change_listener(listener: Callable) -> int`: Adds a change listener and returns its unique ID.
    - `remove_change_listener(listener: Callable | int) -> None`: Removes a change listener, the listener may be given as the original listener object or its unique id (as returned from `add_change_listener`)
    - `get_change_listeners() -> List[Callable]`: Returns a list of all registered change listeners.

    Automatically calls `__on_change__(query)` after `__update__(query)` is called, passing the same query to each registered listener.

    The decorator also adds a private `_change_listeners` dictionary to the class for internal management of listener registrations.

    Note: This decorator modifies the class in-place and requires the class to define `__update__` and `__on_change__` methods. The `__update__` method must accept a query argument, and `__on_change__` is expected to be called with a query argument indicating the change made.

    Usage:
        @change_listener_decorator
        class MyClass:
            ...

    This adds robust change tracking and notification capabilities to classes dealing with dynamic data, particularly useful for XML data management scenarios.
    """

    # Store original __update__ for wrapping
    original_update = cls.__update__

    # Store original __init__ for wrapping
    original_init = cls.__init__

    # Define a new __init__ method that modifies instance-level fields
    def __init_wrapper(self, *args, **kwargs):
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
        self._change_listeners = {}

    cls.__init__ = __init_wrapper

    # Define the add_change_listener method
    def add_change_listener(self, listener: Callable) -> int:
        # Inspect the signature of the listener to ensure it has exactly two parameters
        sig = inspect.signature(listener)
        params = sig.parameters.values()
        # Check if the listener accepts exactly two parameters
        if len(params) < 2:
            raise ValueError(
                "Listener must be a callable that accepts at least two positional arguments, e.g. `def my_change_listener(query, response): ...`"
            )
        listener_id = id(listener)
        self._change_listeners[listener_id] = listener
        return listener_id

    cls.add_change_listener = add_change_listener

    # Define the remove_change_listener method
    def remove_change_listener(self, listener: Callable | int) -> None:
        if isinstance(listener, int):
            listener_id = listener
        else:
            listener_id = id(listener)
        if listener_id in self._change_listeners:
            del self._change_listeners[listener_id]

    cls.remove_change_listener = remove_change_listener

    # Define the get_change_listeners method
    def get_change_listeners(self) -> List[Callable]:
        return list(self._change_listeners.values())

    cls.get_change_listeners = get_change_listeners

    # Wrap the __update__ method to call __on_change__ after execution
    def __update_wrapper(self, query):
        response = original_update(self, query)
        self.__on_change__(query, response)
        return response

    cls.__update__ = __update_wrapper

    # Define the __on_change__ method
    def __on_change__(self, query, response):
        for listener in self._change_listeners.values():
            listener(query, response)

    cls.__on_change__ = __on_change__

    return cls
