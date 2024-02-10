from typing import List

import ray
from ray.actor import ActorHandle

from ..agent.agent import Agent


class Environment:
    def __init__(self, ambient, sync=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ambient = ambient
        if isinstance(ambient, ActorHandle):
            self._step = self._step_remote_seq if sync else self._step_remote_aseq
        else:
            self._step = self._step_local_seq if sync else self._step_local_aseq

    def get_agents(self) -> List[ActorHandle | Agent]:
        if isinstance(self._ambient, ActorHandle):
            return ray.get(self._ambient.get_agents.remote())
        else:
            return self._ambient.get_agents()

    def step(self):
        agents = self._step()
        return len(agents) > 0

    def _step_local_seq(self):
        agents = self.get_agents()
        _ = [agent.__sense__(self._ambient) for agent in agents]
        _ = [agent.__cycle__() for agent in agents]
        _ = [agent.__execute__(self._ambient) for agent in agents]
        return agents

    def _step_local_aseq(self):
        agents = self.get_agents()
        for agent in agents:
            agent.__sense__(self._ambient)
            agent.__cycle__()
            agent.__execute__(self._ambient)
        return agents

    def _step_remote_aseq(self):
        # calls sense, cycle, execute, without waiting for agents to finish each phase, "slower" agents may perceive things after other agents have executed their actions.
        agents = self.get_agents()
        refs = []
        refs.extend([agent.__sense__.remote(self._ambient) for agent in agents])
        refs.extend([agent.__cycle__.remote() for agent in agents])
        refs.extend([agent.__execute__.remote(self._ambient) for agent in agents])
        ray.wait(refs, num_returns=len(refs), timeout=1)
        return agents

    def _step_remote_seq(self):
        # calls sense, cycle, execute sequentially, waiting for each agent to finish before proceeding to the next phase
        agents = self.get_agents()

        refs = [agent.__sense__.remote(self._ambient) for agent in agents]
        # wait for sense to complete
        ready, _ = ray.wait(refs, num_returns=len(refs), timeout=1)
        _ = [ray.get(obj) for obj in ready]

        refs = [agent.__cycle__.remote() for agent in agents]
        # wait for cycle to complete
        ready, _ = ray.wait(refs, num_returns=len(refs), timeout=1)
        _ = [ray.get(obj) for obj in ready]

        refs = [agent.__execute__.remote(self._ambient) for agent in agents]
        # wait for execute to complete
        ready, _ = ray.wait(refs, num_returns=len(refs), timeout=1)
        _ = [ray.get(obj) for obj in ready]

        # TODO handle exceptions properly here!

        return agents
