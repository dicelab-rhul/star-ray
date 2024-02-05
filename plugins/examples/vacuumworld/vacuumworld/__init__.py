""" Run this file to see the demo, see README.md for details. """

import ray
import random
import pathlib
from jinja2 import Environment as JEnv, FileSystemLoader

from icua2.environment import Environment, Ambient
from icua2.environment.xml import XMLAmbient, QueryXPath, QueryXML
from icua2.event.responseevent import Response
from icua2.plugin.pygame import SVGAvatar
from icua2.event import *
from icua2.agent import Actuator, Sensor, Agent

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


def load_svg(cell_size=80, nm=(8, 8)):
    template_dir = str(pathlib.Path(__file__).parent)
    env = JEnv(loader=FileSystemLoader(template_dir))
    template = env.get_template("vacuumworld.svg")
    width = cell_size * nm[0]
    height = cell_size * nm[1]
    return template.render(width=width, height=height, cell_size=cell_size)


class VacuumWorldSensor(Sensor):
    pass


class VacuumWorldActuator(Actuator):
    @Actuator.action
    def attempt_turn(self):
        pass

    @Actuator.action
    def attempt_move(self):
        pass

    @Actuator.action
    def attempt_clean(self):
        pass


@ray.remote
class VacuumWorldAgent(Agent):
    def __cycle__(self):
        pass


@ray.remote
class VacuumWorldAmbient(XMLAmbient):
    def __init__(self, agents):
        svg_code = load_svg()
        super().__init__(agents, svg_code, namespaces=NAMESPACES)

    def __query__(self, query):
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
            raise ValueError(f"Unknown event type {type(query)}")

    def _handle_exit(self, _):
        self.kill()


class VacuumWorldEnvironment(Environment):
    def __init__(self):
        avatar = SVGAvatar.remote()  # pylint: disable=no-member
        ambient = VacuumWorldAmbient.remote([avatar])  # pylint: disable=no-member
        super().__init__(ambient)

    def run(self):
        running = True
        while running:
            running = self.step()


if __name__ == "__main__":
    env = VacuumWorldEnvironment()
    env.run()
