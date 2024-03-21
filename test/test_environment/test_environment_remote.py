# pylint: disable=E1101
import ray
import asyncio
from star_ray import Environment, Ambient, Agent, ActiveActuator, ActiveSensor, Event


@ray.remote  # when using remote agents, it is important that the ambient is also remote!
class MyAmbient(Ambient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 0

    def __select__(self, action):
        pass  # print("sense", action)

    def __update__(self, action):
        pass  # print("act", action)


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
class MyAgentRemote(Agent):

    def __init__(self):
        super().__init__([MySensor()], [MyActuator()])

    def __cycle__(self):
        print("cycle remote: ", self.id)


class MyAgentLocal(Agent):

    def __init__(self):
        super().__init__([MySensor()], [MyActuator()])

    def __cycle__(self):
        print("cycle local: ", self.id)


# nothing async is actually happening in this agent, but its just for demo purposes.
# one could imagine that in __cycle__ for example, the agent was accessing some external resource.
# it is not clear how this should be implemented more generally - should the environment always be mediating this kind of thing?
# maybe the agent needs to read a file to restore its own state, etc.
class MyAgentLocalAsync(Agent):

    def __init__(self):
        super().__init__([MySensor()], [MyActuator()])

    async def __cycle__(self):
        # this should mean that the print always happens last (~1 second after the other two agents)
        await asyncio.sleep(1)
        print("cycle local async: ", self.id)
        print()

    async def __execute__(self, state):
        return super().__execute__(state)

    async def __sense__(self, state):
        return super().__sense__(state)


ray.init()

agent1 = MyAgentRemote.remote()
agent2 = MyAgentLocal()
agent3 = MyAgentLocalAsync()

ambient = MyAmbient.remote([agent1, agent2, agent3])
environment = Environment(ambient, wait=1)

environment.run()
