from star_ray import Environment, Ambient, Agent, ActiveActuator, ActiveSensor, Event


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


class MyAgent(Agent):

    def __init__(self):
        super().__init__([MySensor()], [MyActuator()])

    def __cycle__(self):
        print("cycle: ", self.id)


agent1 = MyAgent()

ambient = MyAmbient([agent1])
environment = Environment(ambient, wait=1)
environment.run()
