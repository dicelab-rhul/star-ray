""" Run this file to see the demo, see README.md for details. """

import os

os.environ["RAY_DEDUP_LOGS"] = "0"

import ray

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


from star_ray.environment import Environment, Ambient
from star_ray.plugin.xml import XMLAmbient, QueryXPath, QueryXML, XMLState
from star_ray.event.responseevent import Response
from star_ray.plugin.pygame import SVGAvatar
from star_ray.event import *
from star_ray.agent import Actuator, Sensor, Agent

from star_ray_web import WebSVGAvatar

_LOGGER = logging.getLogger(__package__)

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


@ray.remote
class MatBIIAvatar(WebSVGAvatar):

    pass


@ray.remote
class MatBIIAmbient(XMLAmbient):
    def __init__(self):
        avatar = MatBIIAvatar.remote()
        svg_file_path = Path(__file__).parent.joinpath("matbii.svg.jinja")
        state_file_path = Path(__file__).parent.joinpath("state.json")
        with open(state_file_path, "r") as json_file:
            data = json.load(json_file)
        with open(svg_file_path, "r") as svg_file:
            svg_template = svg_file.read()

        template = Template(svg_template)
        rendered_svg = template.render(**data)
        super().__init__([avatar], rendered_svg, namespaces=NAMESPACES)

    def __query__(self, query):
        if isinstance(query, QueryXPath):
            return super().__query__(query)
        elif isinstance(query, MouseMotionEvent):
            pass  # return self._handle_mouse_motion_event(query)
        elif isinstance(query, MouseButtonEvent):
            self._handle_mouse_button_event(query)
        elif isinstance(query, KeyEvent):
            pass  # return self._handle_key_event(query)
        elif isinstance(query, ExitEvent):
            self._handle_exit(query)
        else:
            _LOGGER.warning(f"Unknown event type {type(query)}")

    def _handle_mouse_button_event(self, event):
        print(event)
        # TODO: The click event does not always fire properly because the SVG is continuously being updated in the browser.
        # https://github.com/dicelab-rhul/star-ray/issues/1
        # We use DOWN rather than CLICK here to avoid this issue - a fix is quite complex, and probably requires that the
        if event.button == 0 and event.status == MouseButtonEvent.DOWN:  # left click
            # check the element id
            if event.target:
                print(event.target)

    def _handle_exit(self, _):
        self.kill()


class MatBIIEnvironment(Environment):
    def __init__(self):
        ambient = MatBIIAmbient.remote()  # pylint: disable=no-member
        super().__init__(ambient)


if __name__ == "__main__":
    # ray.init()

    env = MatBIIEnvironment()
    while True:
        time.sleep(0.1)
        # start_time = time.time()
        running = env.step()
        # end_time = time.time()
        # elapsed_time = end_time - start_time
        # print(f"The function took {elapsed_time} seconds to complete.")
