import types


__all__ = ("SliceType", "EllipsisType")


class SliceType:
    """This type is used in place of the built-in `slice` type to be compatible with pydantic validation.

    NOTE: I plan to create a pull request in pydantic to support the `slice` type by default (as well as the `Ellipsis` type)
    """

    def __init__(self, start: int, stop: int, step: int = None):
        self.start = start
        self.stop = stop
        self.step = step

    def get_value(self) -> slice:
        return slice(self.start, self.stop, self.step)


class EllipsisType:

    def get_value(self) -> types.EllipsisType:
        return ...
