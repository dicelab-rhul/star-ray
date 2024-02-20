""" Run this file to see the demo, see README.md for details. """

import os

os.environ["RAY_DEDUP_LOGS"] = "0"

import ray
from typing import Any, List, Dict
from pathlib import Path
from textwrap import dedent
from dataclasses import astuple, dataclass
import random
import time
import json
import math
import re
import logging
from jinja2 import Template

from ast import literal_eval


from star_ray.typing import Event
from star_ray.environment import Environment, Ambient
from star_ray.plugin.xml import XMLAmbient, QueryXPath, QueryXML, XMLState
from star_ray.environment.history import history

from .avatar_web import MATBIIAvatar

_LOGGER = logging.getLogger(__package__)

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

DEFAULT_SVG_TEMPLATE_DATA_PATH = Path(__file__).parent.joinpath("state.json")
DEFAULT_SVG_TEMPLATE_PATH = Path(__file__).parent.joinpath("matbii.svg.jinja")


@dataclass
class VariableQuery(Event):
    #  this is a template that will takes a single variable "{{state}}". After rendering this will be used as the new state of the given variable.
    state: str

    def render(self, state):
        return literal_eval(Template(self.state).render(state=state))


class Variable:

    def __init__(
        self,
        name: str,
        state: Any,
        element_id: str,
        attributes: Dict[str, str],
    ):
        self._name = name
        self._state = state

        self._element_id = element_id
        self._attributes = {attr: Template(value) for attr, value in attributes.items()}

    def to_xml_query(self, query: VariableQuery):
        # this is the new state, it will now be used to update the XML backing variables
        self._state = query.render(self._state)
        # new attributes
        attributes = {
            attr: value.render(self._state) for attr, value in self._attributes.items()
        }
        return QueryXML.new(query.source, self._element_id, attributes=attributes)

    @property
    def name(self):
        return self._name


ID_LIGHT1 = "light-1"
ID_LIGHT2 = "light-2"


LIGHT_VARIABLE = Variable(ID_LIGHT1, 0, ID_LIGHT1, {"fill" : })


@ray.remote
@history()
class MATBIIAmbient(XMLAmbient):
    def __init__(
        self, svg_template_path: str = None, svg_template_data_path: str = None
    ):

        svg_template_path = (
            svg_template_path if svg_template_path else DEFAULT_SVG_TEMPLATE_PATH
        )
        svg_template_data_path = (
            svg_template_data_path
            if svg_template_data_path
            else DEFAULT_SVG_TEMPLATE_DATA_PATH
        )
        with open(svg_template_data_path, "r", encoding="UTF-8") as json_file:
            data = json.load(json_file)
        with open(svg_template_path, "r", encoding="UTF-8") as svg_file:
            svg_template = svg_file.read()

        template = Template(svg_template)
        rendered_svg = template.render(**data)
        avatar = MATBIIAvatar.remote(rendered_svg)  # pylint: disable=E1101
        super().__init__([avatar], rendered_svg, namespaces=NAMESPACES)

    def __select__(self, query):
        if isinstance(query, QueryXPath):
            return super().__select__(query)
        else:
            print(query)

    def kill(self):
        self._history.close()  # pylint: disable=E1101
        super().kill()

    def __update__(self, query):
        if isinstance(query, QueryXPath):
            super().__update__(query)
        pass  # super().__update__(query)
        # pass print(query)
        # elif isinstance(query, MouseMotionEvent):
        #     pass  # return self._handle_mouse_motion_event(query)
        # elif isinstance(query, MouseButtonEvent):
        #     self._handle_mouse_button_event(query)
        # elif isinstance(query, KeyEvent):
        #     pass  # return self._handle_key_event(query)
        # elif isinstance(query, ExitEvent):
        #     self._handle_exit(query)
        # else:
        #     _LOGGER.warning(f"Unknown event type {type(query)}")

    # def _handle_mouse_button_event(self, event):
    #     print(event)
    #     # TODO: The click event does not always fire properly because the SVG is continuously being updated in the browser.
    #     # https://github.com/dicelab-rhul/star-ray/issues/1
    #     # We use DOWN rather than CLICK here to avoid this issue - a fix is quite complex, and probably requires that the
    #     if event.button == 0 and event.status == MouseButtonEvent.DOWN:  # left click
    #         # check the element id
    #         if event.target:
    #             print(event.target)

    def _handle_exit(self, _):
        self.kill()


class MATBIIEnvironment(Environment):
    def __init__(self):
        ambient = MATBIIAmbient.remote()  # pylint: disable=no-member
        super().__init__(ambient)

    def close(self):
        self._ambient.kill.remote()
