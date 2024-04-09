from typing import Any, Tuple
import weakref
from collections import UserDict


class DictObservable(UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callbacks = weakref.WeakSet()

    def _trigger_callbacks(self, key: Any, values: Tuple[Any, Any]):
        for callback in self._callbacks:
            callback(key, values)

    def __setitem__(self, key: Any, value: Any):
        if key in self:
            old_value = self[key]
            super().__setitem__(key, value)
            self._trigger_callbacks(key, (old_value, value))
        else:
            super().__setitem__(key, value)
            self._trigger_callbacks(key, (None, value))

    def __delitem__(self, key: Any):
        if key in self:
            value = self[key]
            super().__delitem__(key)
            self._trigger_callbacks(key, (value, None))

    def add_callback(self, callback):
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        self._callbacks.remove(callback)


# Example usage:
if __name__ == "__main__":

    x = DictObservable()
    x.add_callback(print)
    x[0] = 1
    x.update({0: 2, 1: 3})
    x.pop(0)

    isinstance(x, dict)
