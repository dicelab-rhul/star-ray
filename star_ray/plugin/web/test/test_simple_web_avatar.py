import time
import random

import ray

from star_ray.agent import Sensor, Actuator
from star_ray.event import Event, Response


# This is a fake sensor that just returns some new svg code.
class _StubSensor(Sensor):
    def get(self):
        stub_response = Response.new(
            Event.new(),
            success=True,
            data={
                "root": f"""<svg xmlns="http://www.w3.org/2000/svg"><circle cx="100" cy="100" r="50" fill="{self.random_color()}" onclick="handleMouseClick(event)" /></svg>"""
            },
        )
        return [stub_response]

    def random_color(self):
        # Generate random values for red, green, and blue components
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        # Convert the RGB components to a hexadecimal color string
        hex_color = "#{:02X}{:02X}{:02X}".format(red, green, blue)
        # Return the hexadecimal color string
        return hex_color


class ActuatorWeb(Actuator):
    @Actuator.action
    def attempt_mouse_click(self, web_event):
        print(web_event)
        return None


SVG_CODE = """<svg xmlns="http://www.w3.org/2000/svg"><circle cx="100" cy="100" r="50" fill="blue"/></svg>"""


import time
import ray

from star_ray_web import WebXMLAvatar

ray.init()

avatar = WebXMLAvatar([], [])

while True:
    # avatar.__cycle__.remote()
    time.sleep(2)
