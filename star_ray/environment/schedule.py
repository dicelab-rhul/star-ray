# import asyncio
# from abc import ABC, abstractmethod

# from .ambient import Ambient


# class Task(ABC):

#     @abstractmethod
#     async def __call__(self, ambient, *args, **kwargs):
#         pass

#     def spawn(self):
#         return asyncio.create_task(self())

# class TaskAgent(Task):

#     def __init__(self, ambient, wait=0.0):
#         self._ambient = ambient
#         self._agents = asyncio.Queue()
#         self._wait = wait

#     async def insert(self, agent, index=0):
#         await agent.__initialise__(self._ambient)
#         await self._agents.put(index, agent)

#     async def remove(self, agent):
#         await self._agents.remove(agent) # terminate?
#         await agent.__terminate__(self._ambient)

#     async def __call__(self):
#         async for agent in self._agents:
#             asyncio.sleep(self._wait)
#             await agent.__sense__(self._ambient)
#             await agent.__cycle__()
#             await agent.__execute__(self._ambient)


# class Schedule:

#     def __init__(self):
#         self._tasks = []

#     def add_agent(self, agent, ambient, wait=1.0):
#         if wait > 0.0:
#             task = Schedule._run_wait(ambient, agent, wait=wait)
#         else:
#             task = Schedule._run_no_wait(ambient, agent)
#         self._tasks.append(task)

#     @staticmethod
#     async def _run_no_wait(ambient, agent, **kwargs):
#         await agent.__initialise__(ambient)
#         while ambient.is_alive:  # check that the agent is alive...?


#     @staticmethod
#     async def _run_wait(ambient, agent, wait=1.0, **kwargs):
#         await agent.__initialise__(ambient)
#         while ambient.is_alive:  # check that the agent is alive...?
#             await asyncio.sleep(wait)
#             await agent.__sense__(ambient)
#             await agent.__cycle__()
#             await agent.__execute__(ambient)

#     # def remove_agent(self, agent):
#     # this should kill the agent

#     # async def run(self):
