import ray
from icua2.environment import Environment, Ambient
from icua2.environment.xml import XMLAmbient, QueryXPath
from icua2.event import *

from .avatar import SVGAvatar

MATB2_XML = """<svg id="root" width="200" height="320" xmlns="http://www.w3.org/2000/svg">
    <!-- Background rectangle -->
    <rect width="200" height="320" fill="lightgrey" />
</svg>"""

MATB2_NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}


@ray.remote
class MatB2Ambient(XMLAmbient):
    def __init__(self, agents):
        super().__init__(agents, MATB2_XML, namespaces=MATB2_NAMESPACES)

    def __query__(self, query):
        if isinstance(query, QueryXPath):
            return super().__query__(query)
        elif isinstance(query, MouseMotionEvent):
            # there is nothing to be done with this action (except log it)
            # LOGGER.log_event(event)
            pass
        elif isinstance(query, MouseButtonEvent):
            # queries = self.handle_mouse_button_event(event)
            pass
        elif isinstance(query, KeyEvent):
            # queries = self.handle_keyboard_event(event)
            pass
        elif isinstance(query, ExitEvent):
            self._handle_exit(query)
            # queries = self.handle_exit_event(event)

    def _handle_exit(self, query):
        assert isinstance(query, ExitEvent)
        self.kill()

    def kill(self):
        for agent in self.agents:
            ray.kill(agent, no_restart=True)
        self.agents.clear()


class MatB2Environment(Environment):
    def __init__(self):
        avatar = SVGAvatar.remote()  # pylint: disable=no-member
        ambient = MatB2Ambient.remote([avatar])  # pylint: disable=no-member
        super().__init__(ambient)
        self._i = 0

    def run(self):
        running = True
        while running:
            self._i += 1
            print("step", self._i)
            running = self.step()
