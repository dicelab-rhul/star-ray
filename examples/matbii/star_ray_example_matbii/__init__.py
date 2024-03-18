""" Run this file to see the demo, see README.md for details. """

# pylint: disable=E0401,E0611


import os

os.environ["RAY_DEDUP_LOGS"] = "0"

import ray
from pathlib import Path

import json

import logging
from jinja2 import Template

from star_ray.typing import Event
from star_ray.environment import Environment, Ambient
from star_ray.plugin.xml import (
    XMLAmbient,
    QueryXPath,
    QueryXML,
    QueryXMLTemplated,
    XMLState,
    xml_history,
)

from .const import *
from .agent import MATBIIAgent, MATBIIActuator
from .avatar import MATBIIAvatar

_LOGGER = logging.getLogger(__package__)

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

DEFAULT_SVG_TEMPLATE_DATA_PATH = Path(__file__).parent.joinpath("state.json")
DEFAULT_SVG_TEMPLATE_PATH = Path(__file__).parent.joinpath("matbii.svg.jinja")


@ray.remote
@xml_history()
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
        print(query)
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
