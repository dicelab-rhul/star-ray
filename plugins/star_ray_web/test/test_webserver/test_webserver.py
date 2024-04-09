# pylint: disable=E0401, E0611,
from typing import List
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from star_ray import Ambient, Environment, ActiveActuator, ActiveSensor
from star_ray.agent.component import Component
from star_ray.event import ErrorResponse, SelectResponse, Event, UpdateResponse
from star_ray.agent import _Agent, AgentFactory, attempt
from star_ray.plugin.web import WebServer, WebAvatar, SocketSerdeText
import asyncio


class PingAction(Event):
    pass


class PingActuator(ActiveActuator):

    @attempt(route_events=[str])
    def ping(self, event: str):
        return PingAction()


class PingSensor(ActiveSensor):

    def __sense__(self) -> List[Event]:
        return [Event()]


class MyWebAvatar(WebAvatar):

    async def send(self):
        # here we wait for new observations to be added to the buffer, this happens during the agents cycle (see self.__perceive__)
        value = await self._observation_buffer.get()
        print("send!", value)
        return value

    def handle_actuator_response(self, component: Component, event: UpdateResponse):
        print("actuator response: ", event)
        return str(event)  # send this to the server to test

    def handle_error_response(self, component: Component, event: ErrorResponse):
        print("error response: ", event)
        return None

    def handle_sensor_response(self, component: Component, event: SelectResponse):
        print("sensor response: ", event)
        return str(event)  # we are sending text!


class MyWebAvatarFactory(AgentFactory):

    def __call__(self, *args, **kwargs):
        return MyWebAvatar([PingSensor()], [PingActuator()], serde=SocketSerdeText())


class MyAmbient(Ambient):

    def __init__(self):
        super().__init__([])
        self._state = "hello from server"

    def __select__(self, action):
        print("__SELECT__!", action)
        return SelectResponse(query=action, values={"state": self._state})

    def __update__(self, action):
        print("__UPDATE__!", action)


class MyEnvironment(Environment):

    def __init__(self, ambient, *args, **kwargs):
        super().__init__(ambient, *args, **kwargs)
        self._webserver = WebServer(ambient, MyWebAvatarFactory())
        static_path = Path(__file__).parent.expanduser().resolve()
        static_files = StaticFiles(directory=static_path)
        self._webserver._app.mount("/", static_files)

    def get_schedule(self):
        tasks = super().get_schedule()
        # run the web server :) it is running on the main thread here, so we can just run it as a task.
        # there may be more complex setups where it is run remotely... TODO think about how this might be done.
        # return tasks
        webserver_task = asyncio.create_task(self._webserver.run(port=8888))
        return [webserver_task, *tasks]


# NOTE: connect to http://127.0.0.1:8888/index.html
ambient = MyAmbient()
env = MyEnvironment(ambient, wait=1)
env.run()
