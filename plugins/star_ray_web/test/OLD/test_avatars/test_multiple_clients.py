# pylint: disable=E1101
from collections import defaultdict
from queue import Queue
import ray
from fastapi import FastAPI, WebSocket, Depends, HTTPException, WebSocketDisconnect
from ray import serve

from star_ray.agent import Agent, Sensor, Actuator
from star_ray.environment.ambient import Ambient
from star_ray.environment.environment import Environment

# class WebSensor(Sensor):

#     def __query__(self, ambient):
#         # this sensor does not query the ambient, the data it receives is pushed directly
#         # it must be part of a remote ray actor!
#         pass

#     def get(self):
#         # TODO this needs to be reset every cycle?
#         # this implementation doesnt follow that of a usual sensor, usually `get()` can be called multiple times in the same cycle...
#         result = self._object_refs
#         self._object_refs = []
#         return result

#     def __push__(self, data):
#         self._object_refs.update(data)


class WebActuator(Actuator):

    @Actuator.action
    def attempt(self, action):
        # print("Pushed web action!")
        return action


@ray.remote
class WebAvatar(Agent):
    """TODO"""

    def __init__(self):
        """TODO"""
        super().__init__([], [WebActuator()])

    def push(self, action):
        self.actuators[0].attempt(action)

    def pop(self):
        # return observations ...

    def close(self):
        pass  # kill self

    def __cycle__(self):
        pass  # print("cycle!")


app = FastAPI()


async def authenticate_user(token: str):
    # Placeholder for your authentication logic
    return token  # Assuming token is the user_id for simplicity


@serve.deployment(
    num_replicas=1,
)
@serve.ingress(app)
class WebServer:

    def __init__(self, ambient: ray.actor.ActorHandle, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.ambient = ambient
        self.open_connections = defaultdict(bool)

    @app.websocket("/{token}")
    async def websocket_endpoint(self, websocket: WebSocket, token: str):

        user_id = await authenticate_user(token)
        if not user_id:
            await websocket.close(code=1008)
            return

        await websocket.accept()
        self.open_connections[user_id] = True

        # Ensure the user agent is running
        user_agent = WebAvatar.remote()
        ray.get(self.ambient.add_agent.remote(user_agent))

        try:
            while True:
                data = await websocket.receive_text()
                # print("RECEIVED: ", token, data)
                user_agent.push.remote(data)
        except WebSocketDisconnect:
            self.open_connections[user_id] = False
            ray.get(self.ambient.remove_agent.remote(user_agent))
            print(f"WebSocket disconnected for user {user_id}")


class MyEnvironment(Environment):
    pass


@ray.remote
class MyAmbient(Ambient):

    def __select__(self, query):
        print("select", query)

    def __update__(self, query):
        print("update", query)


ray.init()
serve.start(http_options={"port": 8888, "host": "localhost"})

ambient = MyAmbient.remote([])
webserver = serve.run(WebServer.bind(ambient))
environment = MyEnvironment(ambient)

import time

while True:
    # print("step!")
    time.sleep(1)
    environment.step()
    print(ray.get(ambient.get_agents.remote()))
