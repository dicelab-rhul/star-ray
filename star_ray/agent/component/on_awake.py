from .component import Component


def OnAwake(cls):
    """Decorator that will wrap an `Component` class so that it only runs on its first cycle, after which it will remove itself from the agent it is attached to."""
    if not issubclass(cls, Component):
        raise TypeError(
            f"OnAwake decorator can only be applied to classes that derive {Component}."
        )

    class OnAwakeComponent(cls):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._first_cycle = True

        # TODO type hints?
        def __query__(self, state):
            if not self._first_cycle:
                self._agent.remove_component(self)
                return
            super().__query__(state)
            self._first_cycle = False

    return OnAwakeComponent
