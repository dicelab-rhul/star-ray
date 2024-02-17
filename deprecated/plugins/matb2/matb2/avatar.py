from typing import List
import lxml.etree as ET
import ray
from star_ray.agent import Agent, Sensor, Actuator
from star_ray.environment.xml import QueryXML
from star_ray.event import Event

from star_ray.plugin.pygame import PygameView


class _SVGSensor(Sensor):
    def __sense__(self, *args, **kwargs) -> List[Event]:
        return [QueryXML.new("root", []), QueryXML.new("root", ["width", "height"])]


class _PygameActuator(Actuator):
    @Actuator.action
    def attempt_pygame_action(self, event):
        return event


@ray.remote
class SVGAvatar(Agent):
    def __init__(self):
        super().__init__([_SVGSensor()], [_PygameActuator()])
        self._view = PygameView()

    def __execute__(self, ambient):
        super().__execute__(ambient)
        # this will ensure that the agents actions from this cycle are completed before sensing in the next cycle begins.
        self.actuators[0].get()

    def __cycle__(self):
        perceptions = self.sensors[0].get()

        svg_percept, size_percept = (
            perceptions
            if isinstance(perceptions[0].data["root"], str)
            else perceptions[::-1]
        )
        svg_code = svg_percept.data["root"]
        svg_size = (
            size_percept.data["root"]["width"],
            size_percept.data["root"]["height"],
        )
        self._update_view_size(svg_size)  # in case it has changed...
        self._view.render_svg(svg_code=svg_code)

        actions = self._view.step()
        for action in actions:
            self.actuators[0].attempt_pygame_action(action)

    def _update_view_size(self, size):
        if self._view.size != size:
            self._view.size = size

    def kill(self):
        self._view.close()
        ray.actor.exit_actor()