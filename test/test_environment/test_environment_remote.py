import ray
from star_ray import Environment, Ambient, Agent, ActiveActuator, ActiveSensor, Event


@ray.remote  # when using remote agents, it is important that the ambient is also remote!
class MyAmbient(Ambient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 0

    def __select__(self, action):
        print("sense", action)

    def __update__(self, action):
        print("act", action)


class MoveAction(Event):
    pass


class SenseAction(Event):
    pass


class MyActuator(ActiveActuator):

    def __attempt__(self):
        return [MoveAction.new(self.id)]


class MySensor(ActiveSensor):

    def __sense__(self):
        return [SenseAction.new(self.id)]


@ray.remote
class MyAgent(Agent):

    def __init__(self):
        super().__init__([MySensor()], [MyActuator()])

    def __cycle__(self):
        print("cycle: ", self.id)


ray.init()

agent1 = MyAgent.remote()

ambient = MyAmbient.remote([agent1])
environment = Environment(ambient, wait=1)
environment.run()
