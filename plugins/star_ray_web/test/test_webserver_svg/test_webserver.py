# pylint: disable=E0401, E0611,
from dataclasses import dataclass, astuple
import pathlib
from typing import List, Tuple

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from star_ray import Ambient, Environment, ActiveActuator, ActiveSensor
from star_ray.event import SelectResponse, UpdateResponse
from star_ray.agent import Agent, AgentFactory
from star_ray.plugin.web import WebServer, WebAvatar

from star_ray.event import MouseButtonEvent, Event
import asyncio
import json
import math
import random


@dataclass
class SetColorAction(Event):
    color: str

    @staticmethod
    def new(source: str, color: str):
        if color is None:
            color = SetColorAction.get_random_color()
        return SetColorAction(*astuple(Event.new(source)), color)

    @staticmethod
    def get_random_color():
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        return "#{:02X}{:02X}{:02X}".format(red, green, blue)


@dataclass
class SetPositionAction(Event):
    position: Tuple[float, float]
    strength: float

    @staticmethod
    def new(source: str, position: Tuple[float, float], strength: float = 10.0):
        return SetPositionAction(*astuple(Event.new(source)), position, strength)


class MyActuator(ActiveActuator):

    def __init__(self, strength):
        super().__init__()
        self._strength = strength

    @ActiveActuator.attempt
    def set_color(self, color: str):
        return SetColorAction.new(self.id, color)

    @ActiveActuator.attempt
    def set_position(self, position: Tuple[float, float]):
        return SetPositionAction.new(self.id, position, self._strength)


class MySensor(ActiveSensor):

    def __sense__(self) -> List[Event]:
        return [Event.new(self.id)]  # just use a raw event...


class MyAgent(Agent):

    def __init__(
        self, color_pref="#ffd58b", position_pref=(200, 200), strength=1, patience=100
    ):
        super().__init__([MySensor()], [MyActuator(strength)])
        self.color_pref = color_pref
        self.position_pref = position_pref
        self.cycles_of_annoyance = 0
        self.patience = patience

    def __cycle__(self):
        for observations in self.sensors[0].get_observations():
            if observations.values["color"] != self.color_pref:
                # the agent is getting more annoyed!
                self.cycles_of_annoyance += 1
            else:
                # the agent is happy, the colour is its preference
                self.cycles_of_annoyance = 0

        if self.cycles_of_annoyance > self.patience:
            self.actuators[0].set_color(self.color_pref)  # take action!

        # always try to move the position to my prefered location!
        self.actuators[0].set_position(self.position_pref)


class MyWebAvatar(WebAvatar):

    def attempt(self, data: str):
        # this contains a click event
        data = json.loads(data)
        # set the color to something random!
        self.actuators[0].set_color(None)
        self.actuators[0].set_position((data["x"], data["y"]))

    def perceive(self, component, observation) -> str:
        if isinstance(observation, SelectResponse):
            # this will get the current colour in the ambient, we are sending it to the UI
            return json.dumps(observation.values)
        else:
            # don't do anything with an UpdateResponse
            return None


class MyWebAvatarFactory(AgentFactory):

    def __call__(self, *args, **kwargs):
        return MyWebAvatar([MySensor()], [MyActuator(50)])


class MyAmbient(Ambient):

    def __init__(self):
        super().__init__([MyAgent()])
        self._color = "#000000"
        self._position = (0, 0)

    def __select__(self, action):
        # we only have a single action type, so just always return the color state
        return SelectResponse.new(
            self.id, action, True, {"color": self._color, "position": self._position}
        )

    def __update__(self, action):
        if isinstance(action, SetColorAction):
            self._color = action.color  # set the colour!
            return UpdateResponse.new(self.id, action, True)
        elif isinstance(action, SetPositionAction):
            self._position = MyAmbient.move_towards(
                self._position, action.position, action.strength
            )
            return UpdateResponse.new(self.id, action, True)
        else:
            raise TypeError()

    @staticmethod
    def move_towards(current_pos, target_pos, distance):
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        dist = math.hypot(dx, dy)
        if dist < distance:
            return target_pos
        return (
            current_pos[0] + dx * distance / dist,
            current_pos[1] + dy * distance / dist,
        )


class MyWebServer(WebServer):

    def __init__(self, ambient):
        super().__init__(ambient, MyWebAvatarFactory())
        self._namespace = "myserver"
        static_path = pathlib.Path(__file__).parent.expanduser().resolve()
        static_files = StaticFiles(directory=static_path)
        self._app.mount("/", static_files)


class MyEnvironment(Environment):

    def __init__(self, ambient, *args, **kwargs):
        super().__init__(ambient, *args, **kwargs)
        self._webserver = MyWebServer(ambient)
        self._cycle = 0

    def get_schedule(self):
        tasks = super().get_schedule()
        # run the web server :) it is running on the main thread here, so we can just run it as a task.
        # there may be more complex setups where it is run remotely... TODO think about how this might be done.
        # return tasks
        webserver_task = asyncio.create_task(self._webserver.run(port=8888))
        return [webserver_task, *tasks]

    async def step(self) -> bool:
        self._cycle += 1
        # return False if the simulation should stop? TODO more info might be useful...
        agents = self._ambient.get_agents()
        if self._cycle % 100 == 0:
            print(f"CYCLE: {self._cycle} NUM AGENTS: {len(agents)}")
        await self._step(agents)
        return True


ambient = MyAmbient()
env = MyEnvironment(ambient, wait=0.01)
env.run()
