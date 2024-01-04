from dataclasses import dataclass
from typing import List, Tuple

from svgrenderengine.pygame import PygameView
from svgrenderengine.event import (
    Event,
    QueryEvent,
    MouseMotionEvent,
    MouseButtonEvent,
    KeyEvent,
    ExitEvent,
)
from ...utils.logging import LOGGER
from ...agent import Agent
from .agent import Matb2AgentBase

# ACTION SPACE FOR THE AVATAR!


class Matb2Avatar(Matb2AgentBase):
    """A special kind of agent that represents the user. It is responsible for gathering user input and rendering the state of the given application."""

    def __init__(self):
        super().__init__()
        # this view is shown to the user upon receiving the required percept
        self._view = None
        self._mouse_pressed_on = []
        self._key_pressed_on = []

    def cycle(self, perceptions):
        self.perceive(perceptions)
        self.decide()

    def perceive(self, perceptions):
        for percept in perceptions:
            if percept.data and "_xml" in percept.data:
                if self._view:
                    self._render(percept)
                else:  # a new view should be created
                    self._view = PygameView(
                        width=percept.data["width"], height=percept.data["height"]
                    )
                    self._render(percept)
            else:
                # these are the ResponseEvents of actions that have been taken by the user
                print("reponse: ", percept)

    def decide(self):
        # get the users actions from the view. These will be executed when self.execute is called.
        self._actions = self._view.step()

    def _render(self, percept):
        # TODO check if the width/height have changed...
        svg_code = percept.data["_xml"]
        self._view.render_svg(svg_code)
