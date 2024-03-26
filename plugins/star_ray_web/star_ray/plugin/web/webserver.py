# pylint: disable=E1101
from collections import defaultdict
from typing import get_type_hints
import inspect

from abc import ABC


from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import (
    FastAPI,
    Path,
    WebSocket,
    Depends,
    HTTPException,
    WebSocketDisconnect,
)

import uvicorn
import asyncio

from types import SimpleNamespace

from star_ray.agent import Agent, AgentFactory
from star_ray.environment.ambient import Ambient
from star_ray.environment.environment import Environment

from star_ray.typing import Event

import asyncio
from importlib.resources import files
import logging
import copy
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .auth import authenticate_user
from .webavatar import WebAvatar

WS_TRY_AGAIN = 1013

_STAR_RAY_STATIC_PATH = str(files("star_ray") / "plugin/web/static")
_STAR_RAY_TEMPLATE_PATH = str(_STAR_RAY_STATIC_PATH + "/template")
_STAR_RAY_JS_PATH = str(_STAR_RAY_STATIC_PATH + "/js")

_STAR_RAY_TEMPLATES = Jinja2Templates(directory=_STAR_RAY_TEMPLATE_PATH)
_STAR_RAY_STATIC_FILES = StaticFiles(directory=_STAR_RAY_JS_PATH)
_STAR_RAY_TEMPLATES_DATA_DEFAULT = {
    "handle_mouse_button.js": dict(disable_context_menu=True, debug=False)
}

# _STAR_RAY_JS = [
#     "/static/js/star_ray/websocket.js"
#     "/static/template/star_ray/handle_mouse_button.js"
# ]


class WebServer:

    def __init__(
        self,
        ambient: Ambient,
        avatar_factory: AgentFactory,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._app = FastAPI()
        self.register_routes()
        self._ambient: Ambient = ambient
        self._avatar_factory = avatar_factory
        self._open_connections = defaultdict(bool)
        # this will serve any static js files that are defined in star_ray (e.g. websocket.js)
        self._app.mount("/static/star_ray", _STAR_RAY_STATIC_FILES)

        self._templates_data = dict()
        self._templates = dict()
        self.add_template_namespace(
            "star_ray",
            _STAR_RAY_TEMPLATES,
            copy.deepcopy(_STAR_RAY_TEMPLATES_DATA_DEFAULT),
        )

    def add_template_namespace(
        self,
        namespace: str,
        templates: Jinja2Templates,
        templates_data=None,
    ):
        if templates is None:
            raise ValueError("Argument `templates` cannot be None.")
        if templates_data is None:
            templates_data = dict()
        self._templates_data[namespace] = templates_data
        self._templates[namespace] = templates

    def _get_template_configuration(self, namespace: str, filename: str):
        templates = self._templates.get(namespace, None)
        if templates is None:
            raise ValueError(f"Namespace {namespace} doesnt exist.")
        template_data = self._templates_data.get(namespace, dict()).get(filename, None)
        if template_data is None:
            raise ValueError(
                f"File `{filename}` doesn't exist in namespace {namespace}."
            )
        return dict(
            templates=templates,
            template_data=template_data,
        )

    async def serve_template(
        self,
        request: Request,
        namespace: str = Path(...),
        filename: str = Path(...),
    ):
        print(f"Serving javascript file {namespace}:{filename}")
        config = self._get_template_configuration(namespace, filename)
        templates = config["templates"]
        template_data = config["template_data"]
        context = {"request": request, **template_data}
        content = templates.TemplateResponse(filename, context).body.decode("utf-8")
        media_type = None
        if filename.endswith(".js"):
            media_type = "application/javascript"
        return Response(content=content, media_type=media_type)

    def register_routes(self):
        # self._app.get("/", response_class=HTMLResponse)(self.serve_root)
        self._app.websocket("/{token}")(self.websocket_endpoint)
        self._app.get(
            "/static/template/{namespace}/{filename}",
            response_class=Response,
            # dependencies=[Depends(self._get_template_configuration)],
        )(self.serve_template)

    async def run(self, host="127.0.0.1", port=8888):
        # TODO note that this will run in the main process, we are unlikely to have simultaneous users for this to be an issue.
        # at least for now... setting this up to work with multiple worker processes is challenging.
        # Probably we can use ray serve for this, for now using FastAPI app directly is simpler.

        config = uvicorn.Config(app=self._app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def websocket_endpoint(
        self, websocket: WebSocket, user_id: str = Depends(authenticate_user)
    ):
        if not user_id:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        self._open_connections[user_id] = True
        # create avatar using the the factory provided
        user_agent = self._avatar_factory(user_id)
        assert isinstance(user_agent, WebAvatar)  # some methods are required...
        # add the avatar to the environment (ambient)
        self._ambient.add_agent(user_agent)

        send, receive = WebServer._new_socket_handler(user_agent)
        # Task for receiving data
        receive_task = asyncio.create_task(receive(websocket, user_agent))
        # Task for sending data
        send_task = asyncio.create_task(send(websocket, user_agent))

        # Wait for either task to finish (e.g., due to WebSocketDisconnect)
        _, pending = await asyncio.wait(
            [receive_task, send_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel any pending tasks to clean up
        for task in pending:
            task.cancel()

        self._open_connections[user_id] = False
        self._ambient.remove_agent(user_agent)
        print(f"WebSocket disconnected for user {user_id}")

    @staticmethod
    def _new_socket_handler(avatar: WebAvatar):
        dtype = avatar._protocol_dtype
        # def _get_type_hint(method, arg=1):
        #     type_hints = get_type_hints(method)
        #     signature = inspect.signature(method)
        #     name = list(signature.parameters.keys())[arg]
        #     return type_hints.get(name)

        # dtype_receive = _get_type_hint(avatar.__receive__, arg=1)
        # dtype_send = _get_type_hint(avatar.__send__, arg=1)

        async def receive_text(websocket):
            return await websocket.receive_text()

        async def receive_bytes(websocket):
            return await websocket.receive_bytes()

        async def receive_json(websocket):
            return await websocket.receive_json()

        async def send_text(websocket, data):
            await websocket.send_text(data)

        async def send_bytes(websocket, data):
            await websocket.send_bytes(data)

        async def send_json(websocket, data):
            await websocket.send_json(data)

        dtype_receive_map = {
            "byte": receive_bytes,
            "text": receive_text,
            "json": receive_json,
        }

        dtype_send_map = {"byte": send_bytes, "text": send_text, "json": send_json}

        assert dtype in dtype_receive_map
        assert dtype in dtype_send_map

        _websocket_send = dtype_send_map[dtype]
        _websocket_receive = dtype_receive_map[dtype]

        async def _receive(websocket: WebSocket, user_agent: WebAvatar):
            try:
                while True:
                    data = await _websocket_receive(websocket)
                    await user_agent.__receive__(data)
            except WebSocketDisconnect:
                pass

        async def _send(websocket: WebSocket, user_agent: WebAvatar):
            try:
                while True:
                    data = await user_agent.__send__()
                    await _websocket_send(websocket, data)
            except WebSocketDisconnect:
                pass

        return _send, _receive


#  def __init__(self):
#         super().__init__(MyAmbient(), MyWebAvatarFactory())
#         static_path = str(pathlib.Path(__file__).parent.expanduser().resolve())
#         self._templates = Jinja2Templates(directory=static_path)

#         # --- TODO this should be in the super class?
#         static_path_star_ray = files("star_ray") / "plugin/web/static"
#         self._templates_star_ray = Jinja2Templates(
#             directory=str(static_path_star_ray / "template")
#         )
#         self._app.mount(
#             "/static/js",
#             StaticFiles(directory=str(static_path_star_ray / "js")),
#         )
#         client_side_debug = True
#         self._templates_data_star_ray = {
#             "handle_mouse_button.js": dict(
#                 disable_context_menu=True, debug=client_side_debug
#             )
#         }

#         # ---
#         SCRIPTS = [
#             """<script type="module" src="/static/js/websocket.js"></script>""",
#             """<script type="module" src="/static/template/handle_mouse_button.js"></script>""",
#         ]
#         # include star_ray javascript in the head of the root template
#         self._templates_data = {"/": dict(head="\n".join(SCRIPTS))}

#     def register_routes(self):
#         self._app.get("/", response_class=HTMLResponse)(self.serve_root)
#         self._app.get("/static/template/{js_filename}", response_class=Response)(
#             self.serve_js
#         )
#         return super().register_routes()


#     async def serve_root(self, request: Request):
#         response = self._templates.TemplateResponse(
#             "index.html.jinja",
#             {"request": request, **self._templates_data["/"]},
#         )
#         return response


# def get_default_template_data():
#     """Gets the default Jinja2 template data for use with star_ray_web/static/templates/index.html.jinja

#     Returns:
#         Dict[str, Any]: default template data

#     Usage Example:
#     ```
#     from ray import serve
#     from star_ray_web import WebServer, get_default_template_data
#     serve.start(http_options={"port": 8888})
#     webserver = serve.run(WebServer.bind(template_data=get_default_template_data()))
#     ```
#     """
#     return dict(
#         handle_mouse_button=dict(
#             post_route=ROUTE_MOUSE_BUTTON,
#             disable_context_menu=True,
#         ),
#         handle_mouse_motion=dict(
#             post_route=ROUTE_MOUSE_MOTION,
#         ),
#         handle_visibility=dict(post_route=ROUTE_VISIBILITY_CHANGE),
#         head="",
#         body="",
#     )


# @serve.deployment(
#     num_replicas=1,
#     logging_config=LoggingConfig(enable_access_log=False, log_level="WARNING"),
# )
# @serve.ingress(app)
# class WebServer:
#     def __init__(
#         self,
#         *args: Tuple[Any, ...],
#         template_path: str = None,
#         template_data: Dict[str, str] = None,
#         **kwargs: Dict[str, Any],
#     ):
#         # need to give self to super().__init__ due to decorators... it looks a bit weird I know...
#         super().__init__(self, *args, **kwargs)
#         self._logger = logging.getLogger("ray.serve")
#         self._socket_handlers = {}
#         self._templates_path = (
#             str(files(__package__).joinpath("static"))
#             if template_path is None
#             else template_path
#         )
#         self._template_data = dict() if template_data is None else template_data
#         self._event_buffer = _EventBuffer(maxsize=EVENT_BUFFER_MAX_SIZE)

#     @app.get("/", response_class=HTMLResponse)
#     async def index(self, request: Request) -> str:
#         # in line javascript to avoid static file caching issues after modification
#         templates = Jinja2Templates(directory=self._templates_path)
#         response = templates.TemplateResponse(
#             "templates/index.html.jinja",
#             {"request": request, **self._template_data},
#         )
#         return response

#     @app.post(f"/{ROUTE_MOUSE_BUTTON}")
#     async def on_mouse_button(self, request: Request) -> str:
#         try:
#             data = await request.json()
#             position = (data["position"]["x"], data["position"]["y"])
#             button = data["button"]
#             status = MouseButtonEvent.status_from_string(data["status"])
#             target = data["id"]
#             target = target if len(target) > 0 else None
#             await self._add_event(
#                 MouseButtonEvent.new(
#                     source=request.client.host,
#                     button=button,
#                     position=position,
#                     status=status,
#                     target=target,
#                 )
#             )
#             return JSONResponse(content={})
#         except Exception as e:
#             self._logger.exception("Invalid post request.")
#             return JSONResponse(content={"error": str(e)}, status_code=500)

#     @app.post("/on_mouse_motion")
#     async def on_mouse_motion(self, request: Request) -> str:
#         try:
#             data = await request.json()
#             position = (data["position"]["x"], data["position"]["y"])
#             relative = (data["relative"]["x"], data["relative"]["y"])
#             target = data["id"]
#             target = target if len(target) > 0 else None
#             await self._add_event(
#                 MouseMotionEvent.new(
#                     source=request.client.host,
#                     position=position,
#                     relative=relative,
#                     target=target,
#                 )
#             )
#             return JSONResponse(content={})
#         except Exception as e:
#             self._logger.exception("Invalid post request.")
#             return JSONResponse(content={"error": str(e)}, status_code=500)

#     @app.post(f"/{ROUTE_VISIBILITY_CHANGE}")
#     async def on_visibility_change(self, request: Request) -> str:
#         try:
#             data = await request.json()
#             if data["visibility"] == "visible":
#                 # trigger an event
#                 await self._add_event(
#                     VisibilityEvent.new_visible(source=request.client.host)
#                 )
#             elif data["visibility"] == "hidden":
#                 await self._add_event(
#                     VisibilityEvent.new_hidden(source=request.client.host)
#                 )
#             else:
#                 raise ValueError(
#                     f"Invalid value for `visibility` {data['visibility']}, valid values include: [`visible`, `hidden`]"
#                 )
#             return JSONResponse(content={})
#         except Exception as e:
#             self._logger.exception("Invalid post request.")
#             return JSONResponse(content={"error": str(e)}, status_code=500)

#     @app.websocket("/{route_id}")
#     async def _websocket_router(self, websocket: WebSocket, route_id: str):
#         if not route_id in self._socket_handlers.keys():
#             await websocket.close(
#                 code=WS_TRY_AGAIN
#             )  # close the connect and request that the client tries to connect again
#             raise MissingWebSocketHandler(route_id)
#         await self._socket_handlers[route_id].open(websocket)

#     def add_web_socket_handler(
#         self, route, replace=False, socket_handler: WebSocketHandler = None
#     ):
#         if not replace and route in self._socket_handlers:
#             raise ValueError(f"socket handler already exists for route: {route}.")
#         else:
#             socket_handler = WebSocketHandler(route)
#             self._socket_handlers[route] = socket_handler

#     def update_socket(self, route, message):
#         self._socket_handlers[route].update(message)

#     async def _add_event(self, event):
#         await self._event_buffer.put(event)

#     def get_events(self):
#         # this should be called remotely to pop from the event queue.
#         return self._event_buffer.get_all_nowait()
