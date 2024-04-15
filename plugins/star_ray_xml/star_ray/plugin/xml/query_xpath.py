# pylint: disable=[I1101,W0212,W0221]


from typing import List, Dict, Any
from lxml import etree as ET

from star_ray.event import Event, ActiveObservation
from .xml_state import XMLState


class QueryXPath(Event):
    xpath: str
    attributes: List[str] | Dict[str, Any] | str

    def __select__(
        self,
        state: XMLState,
        **kwargs,
    ) -> ActiveObservation:
        if not isinstance(self.attributes, list):
            raise TypeError(
                f"Invalid type {type(self.attributes)} for SELECT query attributes."
            )
        results = XMLState._select(self, state)
        return ActiveObservation(action_id=self, values=results)

    def __update__(
        self,
        state: XMLState,
        **kwargs,
    ) -> ActiveObservation:
        if not isinstance(self.attributes, dict | str):
            raise ValueError(
                f"Invalid type {type(self.attributes)} for UPDATE query attributes, must be `dict` or `str`."
            )
        results = XMLState._update(self, state)
        return ActiveObservation(action_id=self, values=results)
