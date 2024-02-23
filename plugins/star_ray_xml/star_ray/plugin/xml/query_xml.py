# pylint: disable=[I1101,W0212,W0221, W0237]

from dataclasses import astuple
from typing import List, Dict, Any

from .query_xpath import QueryXPath
from star_ray.event import ErrorResponse, SelectResponse, UpdateResponse


class QueryXML(QueryXPath):

    @staticmethod
    def new(
        source: str, element_id: str, attributes: str | List[str] | Dict[str, Any]
    ) -> "QueryXML":
        assert isinstance(attributes, (list, dict, str))
        xpath = f".//*[@id='{element_id}']"
        return QueryXML(*astuple(QueryXPath.new(source, xpath, attributes)))

    def __select__(self, *args, **kwargs) -> SelectResponse | ErrorResponse:
        # TODO catch exceptions here
        response = super().__select__(*args, **kwargs)
        return _validate_select_response(response, self)

    def __update__(self, *args, **kwargs) -> UpdateResponse | ErrorResponse:
        # TODO catch exceptions here
        return super().__update__(*args, **kwargs)

    @property
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


def _validate_select_response(response: SelectResponse, query: QueryXPath):
    if response.success:
        _validate_xml_element_length(query, response.values)
        response.data = (query.element_id, response.values[0])
    return response
