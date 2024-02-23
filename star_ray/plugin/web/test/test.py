""" Run this file to see the demo, see README.md for details. """

import ray
import random

from star_ray.environment import Environment, Ambient
from star_ray.environment.xml import XMLAmbient, QueryXPath, QueryXML
from star_ray.event.responseevent import Response
from star_ray_web import AvatarWeb

from star_ray.event import *

XML = """<svg id="root" width="640" height="640" xmlns="http://www.w3.org/2000/svg">
    <!-- Background rectangle -->
    <rect id="background" width="640" height="640" fill="lightgrey" />
    <!-- Mouse tracker circle -->
    <circle id="circle" cx="320" cy="320" r="60" fill="red" />
</svg>"""

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

# star-ray
# <Simulation Testbed for Agent Research>_ray


@ray.remote
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
            raise ValueError(f"Unknown event type {type(query)}")

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
        new_query = QueryXML.new("circle", {"fill": self.random_color()})
        response = super().__query__(new_query)
        response.query_id = query.id  # match it to the original query
        return response

    def _handle_mouse_button_event(self, query: MouseButtonEvent):
        if query.status == "released":
            select_query = QueryXML.new("circle", ["r"])
            radius = self.__query__(select_query).data["circle"]["r"]
            delta = (query.button - 2) * 10
            new_query = QueryXML.new("circle", {"r": max(10, radius - delta)})
            response = super().__query__(new_query)
            response.query_id = query.id  # match it to the original query
            return response
        else:
            # pressing has no effect
            return Response.new(query, True, {})

    def _handle_mouse_motion_event(self, query: MouseMotionEvent):
        x, y = query.position
        new_query = QueryXML.new("circle", {"cx": x, "cy": y})
        response = self.__query__(new_query)
        response.query_id = query.id  # match it to the original query
        return response


class MouseTrackerEnvironment(Environment):
    def __init__(self):
        avatar = AvatarWeb.remote()  # pylint: disable=no-member
        ambient = MouseTrackerAmbient.remote([avatar])  # pylint: disable=no-member
        super().__init__(ambient)

    def run(self):
        running = True
        while running:
            running = self.step()

class MouseTrackingAvatar():
    

if __name__ == "__main__":
    env = MouseTrackerEnvironment()
    env.run()
