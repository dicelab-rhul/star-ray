from typing import List
import ray
from .view import PygameView
from ..star_ray_xml import QueryXML

from ...agent import Agent, Sensor, Actuator
from ...event import Event


class _SVGSensor(Sensor):
    def __sense__(self, *args, **kwargs) -> List[Event]:
        return [
            QueryXML.new(self.id, "root", []),
            QueryXML.new(self.id, "root", ["width", "height"]),
        ]


class _PygameActuator(Actuator):
    @Actuator.action
    def attempt_pygame_action(self, event):
        return event


@ray.remote(max_restarts=0, max_task_retries=0)
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
        if not perceptions[0].success:
            raise ValueError(
                "Failed to get svg root for rendering, did you forget to use the id tag? <svg id='root' ...>"
            )

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
