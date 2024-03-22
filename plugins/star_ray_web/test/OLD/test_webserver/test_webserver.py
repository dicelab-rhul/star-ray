# pylint: disable=no-member
import time
from pathlib import Path
from star_ray_web import WebServer, get_default_template_data

import ray
from ray import serve

ray.init()

serve.start(http_options={"port": 8888})
webserver = serve.run(WebServer.bind(template_data=get_default_template_data()))
webserver.open_socket.remote("mysocket1")

while True:
    time.sleep(1)
    webserver.update_socket.remote("mysocket1", "hello from server!")
