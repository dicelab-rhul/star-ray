# pylint: disable=E0401, E0611,
from typing import List
from dataclasses import dataclass, astuple
from star_ray import Ambient, Environment, ActiveActuator, ActiveSensor
from star_ray.event import SelectResponse, Event
from star_ray.agent import AgentFactory
from star_ray.plugin.web import WebServer, WebAvatar
import asyncio


@dataclass
class PingAction(Event):
    pass


class PingActuator(ActiveActuator):

    @ActiveActuator.attempt
    def ping(self):
        return PingAction(*astuple(Event.new(self.id)))


class PingSensor(ActiveSensor):
    pass


class MyWebAvatar(WebAvatar):

    def attempt(self, action: bytes):
        print("PING!")
        if action == "Ping":
            self.actuators[0].ping()

    def perceive(self, component, observation) -> str:
        print("OBSERVATION", component, observation)
        return "hello from server!"


class MyWebAvatarFactory(AgentFactory):

    def new(self, *args, **kwargs):
        return MyWebAvatar([PingSensor()], [PingActuator()])


class MyAmbient(Ambient):

    def __init__(self):
        super().__init__([])
        self._state = "hello from server"

    def __select__(self, action):
        print("__SELECT__!", action)
        return SelectResponse.new(self.id, action, True, {"state": self._state})

    def __update__(self, action):
        print("__UPDATE__!", action)


class MyEnvironment(Environment):

    def __init__(self, ambient, *args, **kwargs):
        super().__init__(ambient, *args, **kwargs)
        self._webserver = WebServer(ambient, MyWebAvatarFactory())

    def get_schedule(self):
        tasks = super().get_schedule()
        # run the web server :) it is running on the main thread here, so we can just run it as a task.
        # there may be more complex setups where it is run remotely... TODO think about how this might be done.
        # return tasks
        webserver_task = asyncio.create_task(self._webserver.run(port=8888))
        return [webserver_task, *tasks]

    async def step(self) -> bool:
        # return False if the simulation should stop? TODO more info might be useful...
        agents = self._ambient.get_agents()
        print("AGENTS:", agents)
        await self._step(agents)
        return True


ambient = MyAmbient()
env = MyEnvironment(ambient, wait=1)
env.run()
