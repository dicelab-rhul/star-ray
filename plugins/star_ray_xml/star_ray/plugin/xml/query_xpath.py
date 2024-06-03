# pylint: disable=[I1101,W0212,W0221]


from typing import List, Dict, Any
from lxml import etree as ET
from pydantic import Field

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


class QueryXPathInsert(QueryXPath):
    index: int = Field(default_factory=lambda: 0)


# TODO these queries should eventually replace QueryXPath.
# Their purpose is clearer and type checking will be easier.
class QueryXPathUpdate(QueryXPath):
    pass  # Dict[str, Any]


class QueryXPathSelect(QueryXPath):
    pass  # List[str]


# TODO https://github.com/quandyfactory/dicttoxml?tab=readme-ov-file this might be useful later!
# also see badgerfish http://badgerfish.ning.com/ a way of converting between json (or python dict) and xml
# https://github.com/alexflanagan/perterfish/blob/master/pesterfish.py python script
class QueryXPathReplace(QueryXPath):
    pass  # str # TODO or some datastructure that maps to XML?
