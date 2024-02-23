# pylint: disable=no-member
import time
import logging

from star_ray_web import WebXMLAvatar

from star_ray.plugin.xml import (
    QueryXML,
    QueryXPath,
    XMLAmbient,
    xml_history,
    QueryXMLHistory,
)
from star_ray.environment import Environment
from star_ray.agent import Agent, Actuator, Sensor

import ray

ray.init()

_LOGGER = logging.getLogger(__package__)

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

XML = """
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Circle 1 -->
        <circle id="circle1" cx="50" cy="50" r="30" fill="red" />
        <!-- Circle 2 -->
        <circle cx="150" cy="50" r="30" fill="green" />
    </g>
        <!-- Rectangle 1 -->
        <rect x="130" y="20" width="50" height="30" fill="orange" />
</svg>
"""


@ray.remote
@xml_history()
class MyAmbient(XMLAmbient):
    pass


class XMLActuator(Actuator):

    def __init__(self):
        super().__init__()
        self._cx = 0

    def __attempt__(self):
        self._cx = (self._cx + 1) % 200
        return [QueryXPath.new(self.id, "//svg:circle", {"cx": self._cx})]


class XMLHistorySensor(Sensor):

    def __sense__(self):
        return [QueryXMLHistory.new(self.id, index=...)]


@ray.remote
class MyAgent(Agent):

    def __init__(self):
        super().__init__([], [XMLActuator()])

    def __cycle__(self):
        pass


@ray.remote
class MyAvatar(WebXMLAvatar):

    def __init__(self, svg):
        super().__init__([XMLHistorySensor()], [], svg=svg)

    def __cycle__(self):
        responses = self.sensors[0].get()
        assert len(responses) == 1  # should only be a single response...
        for xml_change in responses[0].values:
            print(xml_change)
            self._send_dict(xml_change)


avatar = MyAvatar.remote(svg=XML)
ambient = MyAmbient.remote([avatar, MyAgent.remote()], xml=XML, namespaces=NAMESPACES)
environment = Environment(ambient=ambient)

while True:
    time.sleep(1)
    environment.step()
    # webserver.update_socket.remote("mysocket1", "hello from server!")
