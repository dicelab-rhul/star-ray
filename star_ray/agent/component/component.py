from abc import ABCMeta
from ...utils import int64_uuid

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

    @property
    def id(self):
        """Unique identifier for this [`ActiveComponent`].

        Returns:
            (`str`): unique identifier
        """
        return self._id


# TODO implement a similar `attempt` decorator for passive components.
# Its behaviour will be slightly different (there is no action buffer, instead the action can be immediately attempted?)
# The meta class will still work provided the "is_attempt" attribute is placed on the methods.


class Sensor(Component):
    pass


class Actuator(Component):
    pass
