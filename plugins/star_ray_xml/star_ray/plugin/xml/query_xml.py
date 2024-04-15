# pylint: disable=[I1101,W0212,W0221, W0237]

from pydantic import computed_field
from typing import List, Dict, Any
from star_ray.event import Observation, ActiveObservation
from .query_xpath import QueryXPath


class QueryXML(QueryXPath):

    def __init__(
        self,
        element_id: str = None,
        attributes: str | List[str] | Dict[str, Any] = None,
        **kwargs,
    ):
        xpath = f"//*[@id='{element_id}']"
        super().__init__(xpath=xpath, attributes=attributes, **kwargs)

    def __select__(self, *args, **kwargs) -> ActiveObservation:
        response = super().__select__(*args, **kwargs)
        return _validate_select_response(response, self)

    def __update__(self, *args, **kwargs) -> ActiveObservation:
        return super().__update__(*args, **kwargs)

    @property
    @computed_field
    def element_id(self) -> str:
        """The `id` tag of the element to query - this is part of the xpath query: `//*[@id='element_id']`

        Returns:
            str: the element id associated with this query
        """
        return self.xpath[9:-2]


def _validate_xml_element_length(query: QueryXML, values: List[Any]):
    if len(values) == 0:
        raise ValueError(
            f"No element was found with xpath query: {query.xpath}, there was no element with id='{query.element_id}'"
        )
    if len(values) > 1:
        raise ValueError(
            f"More than one element was found with xpath query {query.xpath}, 'id' should be a unique identifier."
        )


def _validate_select_response(response: Observation, query: QueryXPath):
    _validate_xml_element_length(query, response.values)
    response.values = response.values[0]
    return response
