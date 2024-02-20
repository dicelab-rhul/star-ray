import ray

from star_ray_web import WebXMLAvatar, get_default_template_data
from star_ray.typing import QueryXPath

from star_ray.agent.sensor import HistorySensor
from star_ray.agent import Actuator


# TODO it would be nice to allow the actuator to decide which input events the avatar will accept.
# This means injecting some javascript into the webserver
class MATBIIActuator(Actuator):

    @Actuator.action
    def attempt(self, event):
        return event


# these prevents text from being selectable
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
            sensors=[HistorySensor(index=..., whitelist_types=[QueryXPath])],
            actuators=[MATBIIActuator()],
            svg=svg,
            template_data=DEFAULT_TEMPLATE_DATA,
        )

    def __cycle__(self):
        for percept in self.sensors[0].get():
            self.send(percept)
            # print(percept)

        for event in self.receive():
            self.actuators[0].attempt(event)
