# pylint: disable=[I1101,W0212,W0221, W0237]

from dataclasses import astuple, dataclass
from typing import List, Dict, Any, Tuple
from jinja2 import Template, UndefinedError

import lxml.etree as ET

from .query_xml import QueryXML, _validate_xml_element_length
from .query_xpath import QueryXPath, _select_element, _update_element
from ._utils import _tostring, _xml_to_primitive

from star_ray.event import ErrorResponse, SelectResponse, UpdateResponse


@dataclass
class QueryXMLTemplated(QueryXML):

    @staticmethod
    def new(
        source: str, element_id: str, attributes: str | List[str] | Dict[str, Any]
    ) -> "QueryXMLTemplated":
        assert isinstance(attributes, (list, dict, str))
        if isinstance(attributes, list) and len(attributes) == 0:
            raise ValueError(
                f"At least one select template must be provided in argument `attributes`. To select an element directly, use `{QueryXML.__name__}` instead."
            )
        return QueryXMLTemplated(*astuple(QueryXML.new(source, element_id, attributes)))

    def __select__(
        self,
        source: str,
        root: ET._Element,
        namespaces: Dict[str, str] = None,
        **kwargs,
    ) -> SelectResponse | ErrorResponse:
        try:
            # evaluate each template in attributes!
            _, element_attributes = _get_element_and_all_attributes(
                self, root, namespaces=namespaces
            )
            # render the SELECT attributes based on the current element data.
            # This means that we can dynamically select based on data in the element we are selecting from.
            select_attributes = _resolve_attribute_templates_select(
                self.attributes, element_attributes
            )
            # select from the element using the resolved attributes
            try:
                result = {x: element_attributes[x] for x in select_attributes}
            except KeyError as e:
                # pylint: disable=W0707
                raise ValueError(
                    f"Missing attribute '{e.args[0]}' on element '{self.element_id}' valid attributes include: {list(element_attributes.keys())}"
                )
        except Exception as e:
            return ErrorResponse.new(source, self, exception=e)
        return SelectResponse.new(source, self, success=True, data=result)

    def __update__(
        self,
        source: str,
        root: ET._Element,
        namespaces: Dict[str, str] = None,
        **kwargs,
    ) -> UpdateResponse | ErrorResponse:
        element, element_attributes = _get_element_and_all_attributes(
            self, root, namespaces=namespaces
        )
        try:
            update_attributes = _resolve_attribute_templates_update(
                self.attributes, element_attributes
            )
            # select from the element using the resolved attributes
            _ = _update_element(update_attributes, element, namespaces=namespaces)
        except Exception as e:
            return ErrorResponse.new(source, self, exception=e)
        return UpdateResponse.new(source, self, success=True)

    @property
    def element_id(self) -> str:
        """The `id` tag of the element to query - this is part of the xpath query: `//*[@id='element_id']`

        Returns:
            str: the element id associated with this query
        """
        return self.xpath[9:-2]


def _resolve_attribute_templates_update(query_attributes, element_attributes):
    element_attributes = {
        _sanitize_attribute_name(k): v for k, v in element_attributes.items()
    }
    if isinstance(query_attributes, str):
        # TODO proper error handling here!
        return Template(query_attributes).render(element_attributes)
    else:
        return dict(
            zip(
                _resolve_iterable(query_attributes.keys(), element_attributes),
                _resolve_iterable(query_attributes.values(), element_attributes),
            )
        )


def _resolve_attribute_templates_select(
    query_attributes, element_attributes
) -> List[str]:
    if not isinstance(query_attributes, list):
        raise TypeError(
            f"Invalid type {type(query_attributes)} for SELECT query attributes."
        )

    # must remove "-" from attribute names so that the template can be properly resolved.
    # In all templates, use "_" in place of "-" for variable names!
    element_attributes = {
        _sanitize_attribute_name(k): v for k, v in element_attributes.items()
    }
    return list(_resolve_iterable(query_attributes, element_attributes))


def _resolve_iterable(attributes, element_attributes):
    try:
        for template in attributes:
            yield Template(template).render(element_attributes)
    except UndefinedError as e:
        msg = e.args[0] if e.args else None
        element_id = element_attributes["id"]
        raise ValueError(
            f"Failed to parse template '{template}'. {msg} on element '{element_id}', valid attributes include: {list(element_attributes.keys())}"
        ) from e


def _get_element_and_all_attributes(
    query: QueryXMLTemplated, root: ET._Element, namespaces: Dict[str, str] = None
) -> Tuple[ET._Element, Dict[str, Any]]:
    elements = root.xpath(query.xpath, namespaces=namespaces)
    _validate_xml_element_length(query, elements)  # this should have length 1
    element = elements[0]
    return element, {k: _xml_to_primitive(v) for k, v in element.attrib.items()}


def _sanitize_attribute_name(name):
    return name.replace("-", "_")
