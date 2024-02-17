from .environment import Environment
from .ambient import Ambient

# from svgrenderengine.engine import SVGApplication
# from svgrenderengine.event import QueryEvent


# class Environment:
#     def __init__(self, application: SVGApplication, agents: List):
#         super().__init__()
#         self.application = application
#         self.agents = {agent.id: agent for agent in agents}

#         self._execute_signal = signal("execute")
#         self._execute_signal.connect(self.execute)
#         self._action_responses = defaultdict(list)

#     def execute(
#         self, sender: str, action: QueryEvent = None, actions: List[QueryEvent] = None
#     ):
#         try:
#             assert sender in self.agents
#         except:
#             raise ValueError(
#                 f"Invalid sender: {sender}, did you call signal.send with the correct arguments? (sender, action = <query>, actions = [<query>, ...])"
#             )  # TODO this should be a warning?
#         # print(action, actions)
#         if not action is None:
#             assert isinstance(action, QueryEvent)
#             assert actions is None  # should not be receiving both action and actions...
#             actions = [action]
#         if not actions is None:
#             for action in actions:
#                 response = self.application.query(action)
#                 if isinstance(response, (list, tuple)):
#                     self._action_responses[sender].extend(response)
#                 else:
#                     self._action_responses[sender].append(response)
#         else:
#             raise ValueError(
#                 f"execute recieved None from sender: {sender}"
#             )  # TODO this should be a warning?

#     def step(self):
#         # sense cycle, this will call self.execute
#         for agent in self.agents.values():
#             agent.sense()

#         # agent cycle, send all action responses that have resulted from sense and execute (on the previous cycle) to the agents
#         for agent_id, agent in self.agents.items():
#             agent.cycle(self._action_responses.get(agent_id, []))
#         self._action_responses.clear()

#         # execute cycle, this will call self.execute
#         for agent in self.agents.values():
#             agent.execute()