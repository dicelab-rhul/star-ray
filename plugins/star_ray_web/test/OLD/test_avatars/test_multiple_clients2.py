# pylint: disable=E1101,E0401,E0611
from collections import defaultdict
from queue import Queue
import ray
from fastapi import FastAPI, WebSocket, Depends, HTTPException, WebSocketDisconnect
from ray import serve

from star_ray.agent import Agent, Sensor, Actuator
from star_ray.environment.ambient import Ambient
from star_ray.environment.environment import Environment

from star_ray.plugin.web import WebServer, WebAvatar
import json
import time


class MyWebAvatar(WebAvatar):

    async def receive(self, data: bytes):
        print(str(data))

    async def send(self) -> bytes:
        print(f"AVATAR {self.id} GETTING DATA FROM SENSORS!")


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


while True:
    # print("step!")
    time.sleep(1)
    environment.step()
    print(ray.get(ambient.get_agents.remote()))
