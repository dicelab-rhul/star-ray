# pylint: disable=E0401, E0611,
from importlib.resources import files
from typing import List
from dataclasses import dataclass, astuple
from fastapi import Request
from star_ray import Ambient, Environment, Actuator, Sensor

from star_ray.agent import AgentFactory
from star_ray.plugin.web import WebServer, WebAvatar
import asyncio
import pathlib


from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


class MyWebAvatar(WebAvatar):

    def attempt(self, action: bytes):
        pass


class MyWebAvatarFactory(AgentFactory):

    def __call__(self, *args, **kwargs):
        return MyWebAvatar([], [])


class MyAmbient(Ambient):

    def __init__(self):
        super().__init__([])

    def __select__(self, action):
        pass  # print("__SELECT__!", action)

    def __update__(self, action):
        pass  # print("__UPDATE__!", action)


class MyWebServer(WebServer):

    def __init__(self):
        super().__init__(MyAmbient(), MyWebAvatarFactory())
        self._namespace = "myserver"
        static_path = str(pathlib.Path(__file__).parent.expanduser().resolve())
        templates = Jinja2Templates(directory=static_path)
        scripts = [
            """<script type="module" src="/static/star_ray/websocket.js"></script>""",
            """<script type="module" src="/static/template/star_ray/handle_mouse_button.js"></script>""",
        ]
        # include star_ray javascript in the head of the root template
        templates_data = {"/index.html.jinja": dict(head="\n".join(scripts), body="")}
        self.add_template_namespace(self._namespace, templates, templates_data)

    def register_routes(self):
        self._app.get("/", response_class=HTMLResponse)(self.serve_root)
        return super().register_routes()

    async def serve_root(self, request: Request):
        filename = "/index.html.jinja"
        config = self._get_template_configuration(self._namespace, filename)
        context = {"request": request, **config["template_data"]}
        response = config["templates"].TemplateResponse(filename, context)
        return response


webserver = MyWebServer()
asyncio.run(webserver.run())
