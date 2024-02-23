# pylint: disable=no-member
import time
import random
import logging
from star_ray.event.exitevent import ExitEvent
from star_ray.event.keyevent import KeyEvent
from star_ray.event.mouseevent import MouseButtonEvent, MouseMotionEvent
from star_ray.event.responseevent import Response
from star_ray_web import WebXMLAvatar

from star_ray.plugin.xml import QueryXML, QueryXPath, XMLAmbient
from star_ray.environment import Environment

import ray

ray.init()

_LOGGER = logging.getLogger(__package__)

XML = """<svg id="root" width="640" height="640" xmlns="http://www.w3.org/2000/svg">
    <!-- Background rectangle -->
    <rect id="background" width="640" height="640" fill="lightgrey" />
    <!-- Mouse tracker circle -->
    <circle id="circle1" cx="240" cy="320" r="60" fill="red" />
    <circle id="circle2" cx="120" cy="320" r="60" fill="blue" />
</svg>"""

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


class MouseTrackerAmbient(XMLAmbient):
    def __init__(self, agents):
        super().__init__(agents, XML, namespaces=NAMESPACES)

    def __query__(self, query):
        if isinstance(query, QueryXPath):
            return super().__query__(query)
        elif isinstance(query, MouseMotionEvent):
            return self._handle_mouse_motion_event(query)
        elif isinstance(query, MouseButtonEvent):
            return self._handle_mouse_button_event(query)
        elif isinstance(query, KeyEvent):
            return self._handle_key_event(query)
        elif isinstance(query, ExitEvent):
            self._handle_exit(query)
        else:
            _LOGGER.warning("Unknown event type %s", type(query))

    def _handle_exit(self, _):
        self.kill()

    def random_color(self):
        # Generate random values for red, green, and blue components
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        # Convert the RGB components to a hexadecimal color string
        hex_color = "#{:02X}{:02X}{:02X}".format(red, green, blue)
        # Return the hexadecimal color string
        return hex_color

    def _handle_key_event(self, query):
        new_query = QueryXML.new("", "circle", {"fill": self.random_color()})
        response = super().__query__(new_query)
        response.query_id = query.id  # match it to the original query
        return response

    def _handle_mouse_button_event(self, query: MouseButtonEvent):
        if query.target != "background":
            if query.status == MouseButtonEvent.UP:
                select_query = QueryXML.new("", query.target, ["r"])
                radius = self.__query__(select_query).data[query.target]["r"]
                delta = (query.button - 1) * 10
                new_query = QueryXML.new(
                    "", query.target, {"r": max(10, radius - delta)}
                )
                response = super().__query__(new_query)
                response.query_id = query.id  # match it to the original query
                return response

        return Response.new(query, True, {})

    def _handle_mouse_motion_event(self, query: MouseMotionEvent):
        # x, y = query.position
        # new_query = QueryXML.new(query.target, {"cx": x, "cy": y})
        if query.target != "background":
            new_query = QueryXML.new("", query.target, {"fill": self.random_color()})
            response = self.__query__(new_query)
            response.query_id = query.id  # match it to the original query
            return response
        return Response.new(query, True, {})


avatar = WebXMLAvatar()
environment = Environment(ambient=MouseTrackerAmbient([avatar]))

while True:
    time.sleep(0.01)
    environment.step()
    # webserver.update_socket.remote("mysocket1", "hello from server!")
