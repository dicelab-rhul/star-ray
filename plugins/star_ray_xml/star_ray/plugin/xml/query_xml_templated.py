# pylint: disable=[I1101,W0212,W0221, W0237]

# TODO this should be made more in line with XMLState interface,
# it seems to implement its own query functionality which is not necessary?

from typing import List, Dict, Any, Tuple
from jinja2 import UndefinedError, Environment
import lxml.etree as ET
from star_ray.event import ActiveObservation


from .query_xml import QueryXML, _validate_xml_element_length
from .xml_state import XMLState
from .utils import xml_to_primitive

# Create a Jinja environment instance, this will be used globally to resolve templated queries
_ENV = Environment()

# Add 'min' function to the global namespace of the environment
_ENV.globals["min"] = min
_ENV.globals["max"] = max


class QueryXMLTemplated(QueryXML):

    def __init__(
        self,
        element_id: str = None,
        attributes: str | List[str] | Dict[str, Any] = None,
        **kwargs,
    ):
        super().__init__(element_id=element_id, attributes=attributes, **kwargs)

    # TODO validator for attributes (see below)
    # @staticmethod
    # def new(
    #     source: str, element_id: str, attributes: str | List[str] | Dict[str, Any]
    # ) -> "QueryXMLTemplated":
    #     assert isinstance(attributes, (list, dict, str))
    #     if isinstance(attributes, list) and len(attributes) == 0:
    #         raise ValueError(
    #             f"At least one select template must be provided in argument `attributes`. To select an element directly, use `{QueryXML.__name__}` instead."
    #         )
    #     return QueryXMLTemplated(*astuple(QueryXML.new(source, element_id, attributes)))

    def __select__(
        self,
        state: XMLState,
        **kwargs,
    ) -> ActiveObservation:
        # evaluate each template in attributes!
        _, element_attributes = _get_element_and_all_attributes(
            self, state._root, namespaces=state._namespaces
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
        return ActiveObservation(action_id=self, values=result)

    def __update__(
        self,
        state: XMLState,
        **kwargs,
    ) -> ActiveObservation:
        element, element_attributes = _get_element_and_all_attributes(
            self, state._root, namespaces=state._namespaces
        )
        update_attributes = _resolve_attribute_templates_update(
            self.attributes, element_attributes
        )
        # select from the element using the resolved attributes
        _ = XMLState._update_element(
            update_attributes,
            element,
            namespaces=state._namespaces,
            parser=state._parser,
        )

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
        return _ENV.from_string(query_attributes).render(element_attributes)
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
            yield _ENV.from_string(template).render(element_attributes)
    except UndefinedError as e:
        msg = e.args[0] if e.args else None
        element_id = element_attributes.get("id", "<UNDEFINED ELEMENT ID>")
        raise ValueError(
            f"Failed to parse template '{template}'. {msg} on element '{element_id}', valid attributes include: {list(element_attributes.keys())}"
        ) from e


def _get_element_and_all_attributes(
    query: QueryXMLTemplated, root: ET._Element, namespaces: Dict[str, str] = None
) -> Tuple[ET._Element, Dict[str, Any]]:
    elements = root.xpath(query.xpath, namespaces=namespaces)
    _validate_xml_element_length(query, elements)  # this should have length 1
    element = elements[0]
    return element, {k: xml_to_primitive(v) for k, v in element.attrib.items()}


def _sanitize_attribute_name(name):
    return name.replace("-", "_")
