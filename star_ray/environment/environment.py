import asyncio
import signal

from .wrapper_state import _State
from .ambient import Ambient
from ..utils import _Future


class Environment:
    def __init__(
        self, ambient: Ambient, sync: bool = True, wait: float = 1.0, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._wait = wait
        self._ambient = _State.new(ambient)
        self._step = self._step_sync if sync else self._step_async

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
            await self.initialise(event_loop)
            await asyncio.gather(*self.get_schedule())

        asyncio.run(_run())

    async def initialise(self, event_loop):
        await self._ambient.initialise()

    def get_schedule(self):
        return [asyncio.create_task(self.loop())]

    async def loop(self):
        running = True
        while running:
            running = await self.step()
            await asyncio.sleep(self._wait)

    async def step(self) -> bool:
        # return False if the simulation should stop? TODO more info might be useful...
        agents = self._ambient.get_agents()
        if len(agents) == 0:
            return False
        await self._step(agents)
        return True

    async def _step_sync(self, agents) -> None:
        await _Future.gather([agent.sense(self._ambient) for agent in agents])
        await _Future.gather([agent.cycle() for agent in agents])
        await _Future.gather([agent.execute(self._ambient) for agent in agents])

    async def _step_async(self, agents) -> None:
        futures = []
        futures.extend([agent.sense(self._ambient) for agent in agents])
        futures.extend([agent.cycle() for agent in agents])
        futures.extend([agent.execute(self._ambient) for agent in agents])
        await _Future.gather(futures)


async def _signal_shutdown(sig, loop):
    print("Received signal {}, shutting down...".format(sig))
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
