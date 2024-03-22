# pylint: disable=no-member
import time
import json
import random
from dataclasses import asdict
from star_ray.event.mouseevent import MouseButtonEvent

from star_ray.plugin.star_ray_xml import QueryXPath, QueryXML
import ray
from star_ray_web.avatar import WebXMLAvatar

ray.init()


class Avatar(WebXMLAvatar):

    def __init__(self, *args, **kwargs):
        svg = """<svg id="root" xmlns="http://www.w3.org/2000/svg"> 
        
        <circle id="circle" r="50" cx="100" cy="100" fill="#ff0000"/>  
        
        <rect id="rect1" x="25" y="10" width="20" height="20" fill="#ff0000"/>  
        <rect id="rect2" x="0" y="10" width="20" height="20" fill="#ff0000"/>  

        <text x="100" y="100"> Some text! </text>
        </svg>"""

        super().__init__(*args, **kwargs, svg=svg)

    def __cycle__(self):
        # update the color of the circle
        query = QueryXML.new("test", "circle", {"fill": self.random_color()})
        self.update(query)

        # update the color of both rects
        query = QueryXPath.new("test", "//svg:rect", {"fill": self.random_color()})
        self.update(query)

        # update the text in the text element
        query = QueryXPath.new(
            "test", "//svg:text/text()", str(random.randint(0, 10000))
        )
        self.update(query)

        actions = self._webserver.get_events.remote().result()
        # attempt each of the actions
        for action in actions:
            if isinstance(action, MouseButtonEvent):
                print(["DOWN", "UP", "CLICK"][action.status])

    def update(self, query):
        query = json.dumps(asdict(query))
        self._webserver.update_socket.remote(self._socket_route, query)

    def random_color(self):
        # Generate random values for red, green, and blue components
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        # Convert the RGB components to a hexadecimal color string
        hex_color = "#{:02X}{:02X}{:02X}".format(red, green, blue)
        # Return the hexadecimal color string
        return hex_color


avatar = Avatar()

while True:
    time.sleep(1)

    avatar.__cycle__()
