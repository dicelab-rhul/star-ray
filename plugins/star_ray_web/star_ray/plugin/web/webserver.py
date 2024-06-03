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
from .webserverbase import WebServerBase

# status codes
WS_TRY_AGAIN = 1013
WS_POLICY_VIOLATION = 1008


class WebServer(WebServerBase):

    def __init__(
        self,
        ambient: Ambient,
        avatar_factory: AgentFactory,
        namespace: str,
        path: str | List[str],
        package_name: str = None,
        **kwargs,
    ):
        super().__init__(namespace, path, package_name=package_name, **kwargs)
        self._ambient: Ambient = ambient
        self._avatar_factory = avatar_factory

    async def websocket_endpoint(
        self, websocket: WebSocket, user_id: str = Depends(authenticate_user)
    ):
        _LOGGER.info("Websocket connecting: {user: %s}", user_id)
        if not user_id:
            await websocket.close(code=WS_POLICY_VIOLATION)
            return
        # create avatar using the factory provided
        avatar = self._avatar_factory(user_id)
        self._ambient.add_agent(avatar)
        await avatar.serve(websocket)
        # the user disconnected, remove the agent
        self._ambient.remove_agent(avatar)
        _LOGGER.info("Websocket disconnected: {user: %s}", user_id)

    def register_routes(self):
        self.app.websocket("/{token}")(self.websocket_endpoint)
        super().register_routes()

    async def run_asyncio(self, host="127.0.0.1", port=8888):
        config = uvicorn.Config(app=self._app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
