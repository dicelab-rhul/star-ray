from star_ray import Environment
from star_ray.application.matb2 import Matb2, Matb2Avatar, Matb2Agent


app = Matb2()
env = Environment(app, [Matb2Avatar(), Matb2Agent()])

while True:
    env.step()
