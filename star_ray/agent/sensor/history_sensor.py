from types import EllipsisType
from typing import List, Type, Optional
from ..component import ActiveSensor
from ...environment.history import QueryHistory


class HistorySensor(ActiveSensor):
    """A simple sensor that gets the most recent event history. This requires the `@history` decorator to be applied to the `Ambient` in use.
    Example:
    ```
    from star_ray.environment.history import history

    @history(...)
    class MyAmbient(Ambient):
        pass
    ```
    """

    def __init__(
        self,
        index: slice | EllipsisType = ...,
        whitelist_types: Optional[List[Type]] = None,
        blacklist_types: Optional[List[Type]] = None,
    ):
        super().__init__()
        self.index = index
        self.whitelist_types = whitelist_types
        self.blacklist_types = blacklist_types

    def __sense__(self):
        return [
            QueryHistory.new(
                self.id,
                index=self.index,
                whitelist_types=self.whitelist_types,
                blacklist_types=self.blacklist_types,
            )
        ]
