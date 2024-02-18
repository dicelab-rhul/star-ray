from ..component import Sensor
from ...environment.history import QueryHistory


class SensorHistory(Sensor):
    """A simple passive sensor that gets the most recent event history. This requires the `@history` decorator to be applied to the `Ambient` in use.
    Example:
    ```
    from star_ray.environment.history import history

    @history(...)
    class MyAmbient(Ambient):
        pass
    ```
    """

    def __sense__(self, *args, **kwargs):
        return [QueryHistory.new(self.id, index=...)]
