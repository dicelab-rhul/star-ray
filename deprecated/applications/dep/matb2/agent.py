# from abc import abstractmethod
# from blinker import signal

# from svgrenderengine.event import Event, QueryEvent

# from ...agent import Agent


# class Matb2AgentBase(Agent):
#     """Base class for agents that are able to interact with the matb2 application."""

#     def __init__(self):
#         super().__init__()
#         self._actions = []  # the actions to execute after each call to cycle
#         self._execute_signal = signal("execute")

#     def sense(self):
#         perceive_action = QueryEvent(
#             *Event.new(),
#             QueryEvent.SELECT,
#             "root",
#             ["width", "height", "_xml"],  # get all xml data for rendering
#         )
#         self._execute_signal.send(self.id, action=perceive_action)

#     def execute(self):
#         # execute all actions that were decided upon
#         self._execute_signal.send(self.id, actions=self._actions)
#         self._actions.clear()  # clear ready for next cycle

#     @abstractmethod
#     def cycle(self, perceptions):
#         pass  # this will be implemented by a subclass. See Matb2Agent and Matb2Avatar.


# class Matb2Agent(Matb2AgentBase):
#     """This agent manages all of the events in the MATB2 system. It will read a schedule file and produce QueryEvent updates to change the interface accordingly."""

#     def __init__(self):
#         super().__init__()
#         self._step = 0

#     def cycle(self, perceptions):
#         self.perceive(perceptions)
#         self.decide()
#         self._step += 1

#     def decide(self):
#         pass
#         # if self._step == 0:
#         #     query = Matb2.update_slider_state(
#         #         self._svg_root, Matb2.get_elements(self._svg_root, "slider-1")[0], 0
#         #     )
#         #     self._actions = [query]

#     def perceive(self, perceptions):
#         for percept in perceptions:
#             if "_xml" in percept.data:
#                 svg_code = percept.data["_xml"]
#                 # self._svg_root = ET.fromstring(svg_code)
#             else:
#                 # these are the ResponseEvents of actions that have been taken by the user
#                 print("reponse: ", percept)
