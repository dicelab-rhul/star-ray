"""Module defines the `Environment` class.

The environment is the container in which the simulation runs and is the simulation entry point. It manages the execution of agents, and has a state (the `Ambient`) which agents read and mutate.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
from .ambient import Ambient, _Ambient
from ..utils import _Future, _LOGGER

if TYPE_CHECKING:
    from ..agent import _Agent


class Environment:
    """The environment is the container in which the simulation runs and is the simulation entry point. It manages the execution of agents, and has a state (the `Ambient`) which agents read and mutate."""

    def __init__(
        self, ambient: Ambient, sync: bool = True, wait: float = 0.05, **kwargs
    ):
        """Constructor.

        Args:
            ambient (Ambient): the state of the environment.
            sync (bool, optional): whether to run the agents synchronously or not. Under the default schedule, if True this means that each cycle method will be gathered together for all agents - i.e. all agents will `__sense__` then `__cycle__` then `__execute__`. If False, then these methods will execute in not particular order, however there will always be a sync point at the start of each cycle.
            wait (float, optional): time to wait between cycles, this leaves room for other async operations if required. Defaults to 0.05.
            **kwargs (dict[str,Any], optional): optional additional arguments.
        """
        super().__init__()
        self._wait = wait
        self._ambient = _Ambient.new(ambient)
        self._step = self._step_sync if sync else self._step_async
        self._cycle = 0

    def run(self):
        """Entry point of the simulation, this call is blocking."""

        async def cancel(tasks: list[asyncio.Task], timeout: float = 1.0):
            for task in tasks:
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=timeout)
                except asyncio.CancelledError:
                    pass  # Ignore the CancelledError exception
                except asyncio.TimeoutError:
                    _LOGGER.warning(f"Task: {task} timed out ({timeout}/s) on cancel")

        async def _run_wait(tasks: list[asyncio.Task]):
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                try:
                    task.result()
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    await cancel(pending)
                    raise e
            if not self._ambient.is_alive:
                await cancel(pending)
            return pending

        async def _run():
            event_loop = asyncio.get_event_loop()
            await self.__initialise__(event_loop)
            pending = self.get_schedule()
            while pending:
                pending = await _run_wait(pending)

        asyncio.run(_run())

    async def __initialise__(self, event_loop: asyncio.AbstractEventLoop):
        """Initialise this environment. Override this for custom initialisation.

        Args:
            event_loop (AbstractEventLoop): the asyncio event loop that is in use.
        """
        await self._ambient.__initialise__()

    def get_schedule(self) -> list[asyncio.Task]:
        """Get all asyncio tasks that are to run during the simulation. This will include one or more schedulars that manange the execution of the agents, but may also include other environmental processes.

        Returns:
            list[Task]: list of tasks that should be run during the simulation.
        """
        return [asyncio.create_task(self._loop())]

    async def _loop(self):
        """Default schedule."""
        running = True
        while running:
            running = await self.step()
            await asyncio.sleep(self._wait)
        _LOGGER.debug("--- MAIN SIMULATION LOOP COMPLETED --- ")

    async def step(self) -> bool:
        """Takes a single step in the simulation. Part of the default schedule.

        Returns:
            bool: whether the simulation should continue
        """
        self._cycle += 1
        agents = self._ambient.get_agents()
        _LOGGER.debug("STEP(%s) - Agents(%s)", self._cycle, str(len(agents)))
        await self._step(agents)
        return self._ambient.is_alive

    async def _step_sync(self, agents: list[_Agent]) -> None:
        """Step all agents with sync points after `__sense__`, `__cycle__`, `__execute__`."""
        await _Future.gather([agent.__sense__(self._ambient) for agent in agents])
        await _Future.gather([agent.__cycle__() for agent in agents])
        await _Future.gather([agent.__execute__(self._ambient) for agent in agents])

    async def _step_async(self, agents: list[_Agent]) -> None:
        """Step all agents with a sync point at the end of each cycle."""
        futures = []
        futures.extend([agent.__sense__(self._ambient) for agent in agents])
        futures.extend([agent.__cycle__() for agent in agents])
        futures.extend([agent.__execute__(self._ambient) for agent in agents])
        await _Future.gather(futures)
