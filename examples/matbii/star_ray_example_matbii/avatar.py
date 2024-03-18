# pylint: disable=E0401,E0611
import ray

from star_ray.plugin.web import WebXMLAvatar, get_default_template_data
from star_ray.plugin.xml import XMLHistorySensor

from .agent import MATBIIActuator

# prevent UI text from being selectable
HEAD = """
<style>
    text {
        -webkit-user-select: none; /* Safari */
        -moz-user-select: none;    /* Firefox */
        -ms-user-select: none;     /* IE/Edge */
        user-select: none;         /* Standard syntax */
    }
</style>
"""
DEFAULT_TEMPLATE_DATA = get_default_template_data()
DEFAULT_TEMPLATE_DATA["head"] += HEAD
DEFAULT_TEMPLATE_DATA["show_keyboard_shortcuts"] = False


@ray.remote
class MATBIIAvatar(WebXMLAvatar):

    def __init__(self, svg):
        super().__init__(
            sensors=[XMLHistorySensor()],
            actuators=[MATBIIActuator()],
            svg=svg,
            template_data=DEFAULT_TEMPLATE_DATA,
        )

    def __cycle__(self):
        for percept in self.sensors[0].get():
            self.send(percept)

        for event in self.receive():
            self.actuators[0].attempt(event)
