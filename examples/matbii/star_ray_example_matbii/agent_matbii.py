from star_ray.agent import Agent


class MATBIIAgent(Agent):

    def __init__(self, sensors, actuators):
        super().__init__(sensors, actuators)

    def __cycle__(self):
        pass
