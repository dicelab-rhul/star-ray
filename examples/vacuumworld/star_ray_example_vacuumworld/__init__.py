""" Run this file to see the demo, see README.md for details. """

import os

os.environ["RAY_DEDUP_LOGS"] = "0"

import ray
from textwrap import dedent
from dataclasses import astuple, dataclass
import random
import time
import math
import re
import logging
from jinja2 import Template


from star_ray.environment import Environment, Ambient
from star_ray.environment.xml import XMLAmbient, QueryXPath, QueryXML
from star_ray.environment.xml.xml_state import XMLState
from star_ray.event.responseevent import Response
from star_ray.plugin.pygame import SVGAvatar
from star_ray.event import *
from star_ray.agent import Actuator, Sensor, Agent

from star_ray_web import WebXMLAvatar

_LOGGER = logging.getLogger(__package__)

ORANGE = "orange"
GREEN = "green"
WHITE = "white"

NORTH = "north"
EAST = "east"
SOUTH = "south"
WEST = "west"

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

SVG_SYMBOL_AGENT = """  
<symbol id="agent" width="1" height="1" viewBox="0 0 200 200">
    <!-- Antenna with light -->
    <line x1="70" y1="30" x2="70" y2="10" stroke="var(--secondary-color)" stroke-width="4"/>
    <circle cx="70" cy="10" r="5" fill="#FFD700"/>

    <!-- Main body -->
    <circle cx="100" cy="100" r="80" fill="var(--primary-color)" stroke="var(--secondary-color)" stroke-width="4"/>

    <!-- Detail lines on body -->
    <circle cx="100" cy="100" r="60" fill="transparent" stroke="var(--secondary-color)" stroke-width="4"/>
    <circle cx="100" cy="100" r="40" fill="transparent" stroke="var(--secondary-color)" stroke-width="4"/>

    <!-- Center sensor -->
    <circle cx="100" cy="70" r="10" fill="var(--secondary-color)"/>

    <!-- Primary Wheels -->
    <rect x="10"  y="80" width="20" height="40" rx="10" fill="#404040"/>
    <rect x="170" y="80" width="20" height="40" rx="10" fill="#404040"/>

    <!-- Additional details -->
    <!-- Top pattern for texture -->
    <circle cx="100" cy="40" r="5" fill="var(--secondary-color)"/>
    <circle cx="110" cy="50" r="5" fill="var(--secondary-color)"/>
    <circle cx="90" cy="50" r="5" fill="var(--secondary-color)"/>
</symbol>
"""
SVG_SYMBOL_DIRT = """
<symbol id="dirt" viewBox="0 0 200 200" width="1" height="1">   
    <circle cx="60" cy="52" r="40" fill="var(--primary-color)" stroke="var(--secondary-color)" stroke-width="4"/>
    <circle cx="150" cy="100" r="30" fill="var(--primary-color)" stroke="var(--secondary-color)" stroke-width="4"/>
    <circle cx="70" cy="152" r="36" fill="var(--primary-color)" stroke="var(--secondary-color)" stroke-width="4"/>
</symbol>"""

SVG_TEMPLATE_GRID = """
    <svg id="root" width="100%" height="100%" viewBox="0 0 {{width + 1}} {{height + 1}}" xmlns="http://www.w3.org/2000/svg">
        
        <!-- define style variables -->
        <style>
            :root   { --primary-color: #FFFFFF; --secondary-color: #000000;}
            .orange { --primary-color: #fe7e0f; --secondary-color: #b1580a;}
            .green  { --primary-color: #87c830; --secondary-color: #5e8c21;}
            .white  { --primary-color: #FFFFFF; --secondary-color: #000000;}
        </style>
        
        <def> 
            <!-- define the dirt symbol for reuse -->
            {{ symbol_dirt }}
            <!-- define the agent symbol for reuse --> 
            {{ symbol_agent }}
        </def>

        <rect x="0" y="0" width = "{{width}}" height = "{{height}}" fill = "white"/>
        <!-- Create grid lines using a for loop -->
        {% for x in range(0, width) %}
            <line x1="{{x}}" y1="0" x2="{{x}}" y2="{{height}}" stroke="black" stroke-width="0.01" />
        {% endfor %}
        {% for y in range(0, height) %}
            <line x1="0" y1="{{y}}" x2="{{width}}" y2="{{y}}" stroke="black" stroke-width="0.01" />
        {% endfor %}

        <!-- Create dirts in the grid -->
        {% for id, config in dirts.items() %}
            <use id="{{id}}" href="#dirt" x="{{config.position[0]}}" y="{{config.position[1]}}" class="{{config.color}}" 
                transform="rotate({{config.orientation}}, {{config.position[0] + 0.5}}, {{config.position[1] + 0.5}})"/>
        {% endfor %}

        <!-- Create agents in the grid -->
        {% for id, config in agents.items() %}
            <use id="{{id}}" href="#agent" x="{{config.position[0]}}" y="{{config.position[1]}}" class="{{config.color}}" 
                transform="rotate({{config.orientation}}, {{config.position[0] + 0.5}}, {{config.position[1] + 0.5}})"/>
        {% endfor %}
    </svg>
"""


@dataclass
class Sense(Event):
    name: str

    @staticmethod
    def new(source, name):
        return Sense(*astuple(Event.new(source)), name)


@dataclass
class Action(Event):
    name: str
    label: str

    @staticmethod
    def new(source, name, label):
        return Action(*astuple(Event.new(source)), name, label)


class VacuumWorldSensor(Sensor):

    def __init__(self, agent: "VacuumWorldAgent"):
        super().__init__()
        self._agent = agent

    def __sense__(self):
        return [Sense.new(self.id, self._agent.name)]


class VacuumWorldActuator(Actuator):

    def __init__(self, agent: "VacuumWorldAgent"):
        super().__init__()
        self._agent = agent

    @Actuator.action
    def turn_left(self):
        return Action.new(self.id, self._agent.name, "turn_left")

    @Actuator.action
    def turn_right(self):
        return Action.new(self.id, self._agent.name, "turn_right")

    @Actuator.action
    def move(self):
        return Action.new(self.id, self._agent.name, "move")

    @Actuator.action
    def clean(self):
        return Action.new(self.id, self._agent.name, "clean")

    @Actuator.action
    def speak(self, message):
        pass  # TODO


@ray.remote
class VacuumWorldAgent(Agent):

    def __init__(self, name):
        super().__init__([VacuumWorldSensor(self)], [VacuumWorldActuator(self)])
        self.position = None
        self.name = name

    def manhattan_dist(self, target_position):
        return (abs(self.position[0] - target_position[0])) + abs(
            self.position[1] - target_position[1]
        )

    def __cycle__(self):
        data = self.sensors[0].get()[0].data
        self.position = data[self.name]["position"]
        print(self.name, self.position)
        dpos = list(
            sorted(
                [
                    item["position"]
                    for _, item in data.items()
                    if item["type"] == "dirt"
                ],
                key=self.manhattan_dist,
            )
        )
        # TODO choose action properly
        self.actuators[0].turn_left()


# this class inherits its functionality from super, this def just makes it remote
@ray.remote
class VacuumWorldAvatar(WebXMLAvatar):
    pass


@ray.remote
class VacuumWorldAmbient(XMLAmbient):
    def __init__(self):
        avatar = VacuumWorldAvatar.remote()  # .remote()  # pylint: disable=no-member
        grid, agents = VacuumWorldAmbient.new_grid()
        super().__init__(agents + [avatar], grid, namespaces=NAMESPACES)

    def __query__(self, query):
        if isinstance(query, Sense):
            return self._handle_sense(query)
        if isinstance(query, Action):
            return self._handle_action(query)
        if isinstance(query, QueryXPath):
            return super().__query__(query)
        elif isinstance(query, MouseMotionEvent):
            pass  # return self._handle_mouse_motion_event(query)
        elif isinstance(query, MouseButtonEvent):
            pass  # return self._handle_mouse_button_event(query)
        elif isinstance(query, KeyEvent):
            pass  # return self._handle_key_event(query)
        elif isinstance(query, ExitEvent):
            self._handle_exit(query)
        else:
            _LOGGER.warning(f"Unknown event type {type(query)}")

    def _handle_action(self, event: Action):
        if event.label == "turn_left":
            # rotate the agent
            result = self.__query__(
                QueryXML.new("environment", event.name, ["transform"])
            )
            print("OLD", result.data[event.name]["transform"])
            # print(result.data[event.name]["transform"])
            rotation_data = list(
                re.search(
                    r"rotate\(\s*(\d+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)",
                    result.data[event.name]["transform"],
                ).groups()
            )
            # print(rotation_data)
            rotation_data[0] = str((int(rotation_data[0]) + 90) % 360)
            new_transform = f"rotate({','.join(rotation_data)})"
            result = result = self.__query__(
                QueryXML.new("environment", event.name, {"transform": new_transform})
            )
            result = self.__query__(
                QueryXML.new("environment", event.name, ["transform"])
            )
            print("NEW", result.data[event.name]["transform"])

    def _handle_sense(self, event: Sense):
        # query = "//svg:use[number(@x) >= 5]"
        query = "//svg:use"
        result = self.__query__(
            QueryXPath.new_select(
                event.source, query, ["x", "y", "id", "href", "class", "transform"]
            )
        )
        return Response.new(
            "environment", event, success=True, data=dict(self._get_sense_data(result))
        )

    def _get_sense_data(self, result):
        for elem in result.data:
            data = dict(
                position=(int(elem["x"]), int(elem["y"])),
                color=elem["class"],
                type=elem["href"][1:],
            )
            if elem["href"] == "#agent":
                data["orientation"] = int(
                    re.search(r"rotate\(\s*([\d.]+)", elem["transform"]).group(1)
                )
            yield elem["id"], data

    @staticmethod
    def new_grid(config=None):
        if config is None:
            config = VacuumWorldAmbient.random_configuration(8, 8, 6, 2)
        agents = [VacuumWorldAgent.remote(id) for id, agent in config["agents"].items()]
        template = Template(SVG_TEMPLATE_GRID)
        return (
            template.render(
                symbol_agent=SVG_SYMBOL_AGENT, symbol_dirt=SVG_SYMBOL_DIRT, **config
            ),
            agents,
        )

    @staticmethod
    def random_configuration(width, height, num_dirts=None, num_agents=None):
        if num_dirts is None:
            num_dirts = max(1, int(width * height * random.random()))
        if num_agents is None:
            num_agents = random.randint(1, int(math.sqrt(width * height)))

        def sample_position():
            return random.randint(0, width - 1), random.randint(0, height - 1)

        def sample_color(white=False):
            return random.choice([ORANGE, GREEN] + ([WHITE] if white else []))

        def sample_orientation():
            return random.randint(0, 3) * 90

        grid = dict(width=width, height=height)
        grid["dirts"] = {
            f"dirt-{i}": {
                "position": sample_position(),
                "color": sample_color(white=False),
                "orientation": sample_orientation(),
            }
            for i in range(num_dirts)
        }
        grid["agents"] = {
            f"agent-{i}": {
                "position": sample_position(),
                "color": sample_color(white=True),
                "orientation": sample_orientation(),
            }
            for i in range(num_dirts)
        }
        return grid

    def _handle_exit(self, _):
        self.kill()


class VacuumWorldEnvironment(Environment):
    def __init__(self):
        ambient = VacuumWorldAmbient.remote()  # pylint: disable=no-member
        super().__init__(ambient)


if __name__ == "__main__":
    # ray.init()

    env = VacuumWorldEnvironment()
    while True:
        time.sleep(1)
        # start_time = time.time()
        running = env.step()
        # end_time = time.time()
        # elapsed_time = end_time - start_time
        # print(f"The function took {elapsed_time} seconds to complete.")
