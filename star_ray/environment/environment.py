import asyncio

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
        async def run_loop():
            running = True
            while running:
                running = await self.step()
                if self._wait:
                    await asyncio.sleep(self._wait)

        asyncio.run(run_loop())

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
