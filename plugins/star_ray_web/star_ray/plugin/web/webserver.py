# pylint: disable=E1101
import asyncio
import copy
import logging

from typing import Any, Dict, List, Tuple
from collections import defaultdict
from importlib.resources import files

from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import (
    FastAPI,
    Path,
    Request,
    WebSocket,
    Depends,
    WebSocketDisconnect,
)

import uvicorn
from star_ray.utils import _LOGGER
from star_ray.agent import AgentFactory
from star_ray.environment.ambient import Ambient
from .auth import authenticate_user
from .webavatar import WebAvatar


# status codes
WS_TRY_AGAIN = 1013

# paths to static resources in this plugin
_STAR_RAY_STATIC_PATH = str(files("star_ray") / "plugin" / "web" / "static")
_STAR_RAY_TEMPLATE_PATH = str(_STAR_RAY_STATIC_PATH + "/template")
_STAR_RAY_JS_PATH = str(_STAR_RAY_STATIC_PATH + "/js")

# serves static files
_STAR_RAY_STATIC_FILES = StaticFiles(directory=_STAR_RAY_JS_PATH)

# file handler for templates
_STAR_RAY_TEMPLATES = Jinja2Templates(directory=_STAR_RAY_TEMPLATE_PATH)
# data for template files.
# NOTE: if the template file is not listed here (but is in _STAR_RAY_TEMPLATES) then an error
# will be thrown when attempting to serve the file.
_STAR_RAY_TEMPLATES_DATA_DEFAULT = {
    "handle_mouse_button.js": dict(disable_context_menu=True, debug=True),
    "handle_keyboard.js": dict(
        debug=True, cancel_arrow_scroll=False, send_key_hold=False
    ),
}


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

    async def websocket_endpoint(
        self, websocket: WebSocket, user_id: str = Depends(authenticate_user)
    ):
        _LOGGER.info("Websocket connecting: {user: %s}", user_id)
        if not user_id:
            await websocket.close(code=1008)
            return
        self._open_connections[user_id] = True
        # create avatar using the factory provided
        avatar = self._avatar_factory(user_id)
        # TODO it would be better to fail earlier...
        assert isinstance(avatar, WebAvatar)
        self._ambient.add_agent(avatar)
        await avatar.serve(websocket)
        # the user disconnected, remove the agent
        self._ambient.remove_agent(avatar)
        self._open_connections[user_id] = False
        _LOGGER.info("WebSocket disconnected: {user: %s}", user_id)

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
                f"File `{filename}` doesn't exist in namespace {namespace}, failed to locate template data."
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
        # TODO we should include some header data here, authentication/user sessions need to be implemented properly!
        _LOGGER.info("Serving javascript file %s : %s", namespace, filename)
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
        )(self.serve_template)

    async def run(self, host="127.0.0.1", port=8888):
        # TODO note that this will run in the main process, we are unlikely to have simultaneous users for this to be an issue.
        # at least for now... setting this up to work with multiple worker processes is challenging.
        # Probably we can use ray serve for this, for now using FastAPI app directly is simpler.

        config = uvicorn.Config(app=self._app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
