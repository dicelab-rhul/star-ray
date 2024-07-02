from __future__ import annotations
import asyncio
import time
import signal
from .ambient import Ambient, _Ambient
from ..utils import _Future, _LOGGER


from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..agent.wrapper_agent import _Agent


class Environment:
    def __init__(
        self, ambient: Ambient, sync: bool = True, wait: float = 1.0, *args, **kwargs
    ):
        super().__init__()
        self._wait = wait
        self._ambient = _Ambient.new(ambient)
        self._step = self._step_sync if sync else self._step_async
        self._cycle = 0

    def run(self):
        async def _run():
            event_loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                event_loop.add_signal_handler(
                    sig,
                    lambda sig=sig: asyncio.create_task(
                        _signal_shutdown(sig, event_loop), name=f"shutdown-signal-{sig}"
                    ),
                )
            await self.__initialise__(event_loop)
            _LOGGER.debug("Environment running...")
            await asyncio.gather(*self.get_schedule())

        asyncio.run(_run())

    async def __initialise__(self, event_loop):
        await self._ambient.__initialise__()
        _LOGGER.debug("Environment initialised successfully.")

    def get_schedule(self):
        return [asyncio.create_task(self.loop())]

    # async def initialise_agents(self):
    #     await _Future.gather(
    #         [
    #             agent.__initialise__(self._ambient)
    #             for agent in self._ambient.get_agents()
    #         ]
    #     )

    async def loop(self):
        # await self.initialise_agents()
        running = True
        while running:
            running = await self.step()
            await asyncio.sleep(self._wait)
        _LOGGER.debug("--- MAIN SIMULATION LOOP COMPLETED --- ")

    async def step(self) -> bool:
        self._cycle += 1
        agents = self._ambient.get_agents()
        _LOGGER.debug("STEP(%s) - Agents(%s)", self._cycle, str(len(agents)))
        t = time.time()
        await self._step(agents)
        print(time.time() - t)
        return self._ambient.is_alive

    async def _step_sync(self, agents: List[_Agent]) -> None:
        await _Future.gather([agent.__sense__(self._ambient) for agent in agents])
        await _Future.gather([agent.__cycle__() for agent in agents])
        await _Future.gather([agent.__execute__(self._ambient) for agent in agents])

    async def _step_async(self, agents: List[_Agent]) -> None:
        futures = []
        futures.extend([agent.__sense__(self._ambient) for agent in agents])
        futures.extend([agent.__cycle__() for agent in agents])
        futures.extend([agent.__execute__(self._ambient) for agent in agents])
        await _Future.gather(futures)


async def _signal_shutdown(sig, loop):
    print("Received signal {}, shutting down...".format(sig))
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
