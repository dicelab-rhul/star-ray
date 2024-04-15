# pylint: disable=E0401, E0611,
from typing import List
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from star_ray import Ambient, Environment, Actuator, Sensor
from star_ray.agent.component import Sensor, Actuator
from star_ray.event import Event, Observation, ActiveObservation, ErrorObservation
from star_ray.agent import _Agent, AgentFactory, attempt
from star_ray.plugin.web import WebServer, WebAvatar, SocketSerdeText
import asyncio


class PingAction(Event):
    pass


class PingActuator(Actuator):

    @attempt(route_events=[str])
    def ping(self, event: str):
        return PingAction()


class PingSensor(Sensor):

    def __sense__(self) -> List[Event]:
        return [Event()]


class MyWebAvatar(WebAvatar):

    def handle_actuator_observation(self, component: Actuator, event: Observation):
        print("actuator observation: ", event)
        return str(event)  # send this to the server to test

    def handle_sensor_observation(self, component: Sensor, event: Observation):
        print("sensor observation: ", event)
        return str(event)


class MyWebAvatarFactory(AgentFactory):

    def __call__(self, *args, **kwargs):
        return MyWebAvatar([PingSensor()], [PingActuator()], serde=SocketSerdeText())


class MyAmbient(Ambient):

    def __init__(self):
        super().__init__([])
        self._state = "hello from server"

    def __select__(self, action):
        print("__SELECT__!", action)
        return ActiveObservation(action_id=action, values={"state": self._state})

    def __update__(self, action):
        print("__UPDATE__!", action)
        return ActiveObservation(action_id=action, values={"ping": True})


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
