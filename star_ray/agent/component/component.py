from abc import ABC
import uuid


class Component(ABC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id: str = str(uuid.uuid4())

    @property
    def id(self):
        """Unique identifier for this [`ActiveComponent`].

        Returns:
            (`str`): unique identifier
        """
        return self._id


class Sensor(Component):
    pass


class Actuator(Component):
    pass
