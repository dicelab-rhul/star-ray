""" Contains the various actions that MATBII agents can take. These are simply convienience classes that wrap [`XPathQuery`], [`XMLQuery`] or [`QueryXMLTemplated`]."""

# pylint: disable=E0401,E0611


from star_ray.plugin.xml import QueryXMLTemplated

from dataclasses import dataclass, astuple

from star_ray_example_matbii import ID_LIGHT1, ID_LIGHT2


@dataclass
class QueryLight(QueryXMLTemplated):

    @staticmethod
    def new_toggle(source: str, light_index: int):
        element_id = [ID_LIGHT1, ID_LIGHT2][light_index]
        attributes = {
            "data-state": "{{1-data_state}}",  # this will toggle "data-state" of the light
            "fill": "{{data_colors[data_state]}}",  # this will set the light fill based on the data-colors attribute
        }
        return QueryLight(
            *astuple(QueryXMLTemplated.new(source, element_id, attributes))
        )
