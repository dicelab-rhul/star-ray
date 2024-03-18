from star_ray.agent import Agent, Actuator


class MATBIIActuator(Actuator):
    """A general purpose actuator which is able to attempt any given action via `attempt(action)`."""

    @Actuator.action
    def attempt(self, event):
        return event


class MATBIIAgent(Agent):
    """Base class for a MATBII agent."""

    def __init__(self, sensors, actuators):
        super().__init__(sensors, actuators)

    def __cycle__(self):
        pass
