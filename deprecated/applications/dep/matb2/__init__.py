# from abc import abstractmethod
# from dataclasses import dataclass
# from typing import List, Tuple
# from blinker import signal
# from lxml import (
#     etree as ET,
# )  # parse the svg oobservation so that actions may be taken on it

# from svgrenderengine.engine import SVGApplication, find_all_clickable_elements_at
# from svgrenderengine.pygame import PygameView
# from svgrenderengine.event import (
#     Event,
#     QueryEvent,
#     MouseMotionEvent,
#     MouseButtonEvent,
#     KeyEvent,
#     ExitEvent,
# )
# from ...utils.logging import LOGGER
# from ...agent import Agent

# from .agent import Matb2AgentBase, Matb2Agent
# from .avatar import Matb2Avatar

# NAMESPACE = "svg_render_engine"
# GREEN = "#95d540"
# RED = "#e6584f"
# LIGHTGREY = "#f5f5f5"

# WARNING_LIGHT_1 = "warning-light-1"
# WARNING_LIGHT_2 = "warning-light-2"
# SLIDER = "slider"
# SLIDER_BOX = "slider-box"

# MATBII_SVG = f"""
# <svg id="root" width="200" height="320" xmlns="http://www.w3.org/2000/svg" xmlns:svgre="{NAMESPACE}">
#     <!-- Background rectangle -->
#     <rect width="200" height="320" fill="{LIGHTGREY}" />

#     <g font-family="Arial" font-size="12" >

#     <!-- Top rectangles -->
#     <rect id="{WARNING_LIGHT_1}" x="10"  y="10" width="80" height="40" fill="{GREEN}" stroke="black" stroke-width="1" svgre:clickable="true" svgre:state="0"/>

#     <text x="40"  y="35" fill="#0500d6" stroke="#0500d6">F5</text>

#     <rect id="{WARNING_LIGHT_2}" x="110" y="10" width="80" height="40" fill="{LIGHTGREY}" stroke="black" stroke-width="1" svgre:clickable="true" svgre:state="0"/>
#     <text x="140"  y="35"  fill="#0500d6" stroke="#0500d6">F6</text>

#         <!-- Segment dividers for vertical rectangles -->
#         <g fill="none" stroke="black" stroke-width="1">

#             {{% for j in range(0, 4)  %}}
#                 <!-- Vertical rectangle -->
#                 <rect id="{SLIDER}-{{{{j}}}}" x="{{{{ 10 + j * 50 }}}}" y="70" width="30" height="220" fill="#add9e6" svgre:clickable="true"/>

#                 <!-- Moveable rect for Vertical rectangle-->
#                 <rect id="{SLIDER_BOX}-{{{{j}}}}" x="{{{{ 10 + j * 50 }}}}" y="150" width="30" height="60" stroke="#4683b2" fill="#4683b2" svgre:state="{{{{150 / 30}}}}"/>

#                 <!-- Dividers for Vertical rectangle -->
#                 {{% for i in range(1, 12) %}}
#                 <rect x="{{{{ 10 + j * 50 }}}}" y="{{{{ 50 + i * 20 }}}}" width="30" height="20"/>
#                 {{% endfor %}}

#                 <!-- Bottom text for Vertical rectangle -->
#                 <text x="{{{{ 10 + j * 50 }}}}" y="310"  fill="#0500d6" stroke="#0500d6">F{{{{j + 1}}}}</text>
#             {{% endfor %}}
#         </g>

#     </g>
# </svg>
# """

# # it is also possible to use QueryEvents directly.

# # def handle_mouse_motion_event(self, event) -> List[QueryEvent]:
# #         # NOTE: 'relative=(0,0)' indicates that the mouse has just moved into the window.
# #         return []  # nothing to do except log the event


# class WarningLightAction(QueryEvent):
#     """This action will toggle a warning light from its failure state to its acceptable state.

#     Args:
#         QueryEvent (_type_): _description_
#     """

#     def __init__(self, warning_light_id):
#         pass  # super().__init__(*Event.create_event(), element_id=warning_light_id, attributes)


# class Matb2(SVGApplication):
#     def __init__(self):
#         super().__init__(svg_code=MATBII_SVG)
#         self._mouse_pressed_on = []

#     def query(self, event: Event):
#         # here we check what kind of query is being used, it may be that we need to
#         # first log the event
#         queries = []
#         if isinstance(event, QueryEvent):
#             queries = [event]
#         elif isinstance(event, MouseMotionEvent):
#             # there is nothing to be done with this action (except log it)
#             LOGGER.log_event(event)
#         elif isinstance(event, MouseButtonEvent):
#             queries = self.handle_mouse_button_event(event)
#         elif isinstance(event, KeyEvent):
#             queries = self.handle_keyboard_event(event)
#         elif isinstance(event, ExitEvent):
#             queries = self.handle_exit_event(event)
#         else:
#             raise ValueError(f"Unknown event: {event} given to application query.")

#         responses = []
#         for query in queries:
#             resp = super().query(query)
#             responses.append(resp)
#             # we dont need to log sense actions and their responses, but log everything else
#             if not "_xml" in query.attributes:
#                 LOGGER.log_event(query)
#                 # LOGGER.log_event(resp) # TODO do we need to log responses? maybe for debugging?

#         return responses

#     def handle_mouse_button_event(self, event) -> List[QueryEvent]:
#         # handle button clicks for each of the parts of the MATBII interface
#         actions = []
#         clickable_elements = find_all_clickable_elements_at(
#             self.element_tree_root, event.position
#         )
#         if event.status == "pressed":  # TODO make constant
#             assert len(self._mouse_pressed_on) == 0
#             for element in clickable_elements:
#                 element_id = element.get("id", None)
#                 self._mouse_pressed_on.append(element_id)
#         elif event.status == "released":  # TODO make constant
#             for element in clickable_elements:
#                 element_id = element.get("id", None)
#                 if element_id in self._mouse_pressed_on:
#                     action = Matb2.handle_click_event(self.element_tree_root, element)
#                     if action:
#                         actions.append(action)
#             self._mouse_pressed_on.clear()
#         return actions

#     def handle_keyboard_event(self, event) -> List[QueryEvent]:
#         return []

#     def handle_exit_event(self, event) -> List[QueryEvent]:
#         # TODO
#         # self._view.close()  # TODO destroy this agent aswell? perhaps an action needs to be taken here...
#         return []

#     # @staticmethod
#     # def update_slider_state(root_element, element, new_state):
#     #     element_id = element.get("id")
#     #     # trying to update an element that is not a slider?
#     #     assert "slider" in element_id
#     #     query = QueryEvent(
#     #         *Event.new(),
#     #         action=QueryEvent.UPDATE,
#     #         element_id=element_id,
#     #         attributes=dict(),
#     #     )
#     #     # the update query is happening on the box, not the clickable slider
#     #     query.element_id = f"{SLIDER_BOX}-{query.element_id.split('-')[-1]}"
#     #     # get the box element from the root element
#     #     box_element = root_element.xpath(f".//*[@id='{query.element_id}']")[0]
#     #     box_height = int(box_element.get("height"))
#     #     inc = box_height / 3
#     #     inc_steps = int(element.get("height")) / inc  # total number of steps...
#     #     new_state = max(min(new_state, inc_steps - 1), 1)  # clamp the new state...
#     #     query.attributes["y"] = str(int(element.get("y")) + (new_state - 1) * inc)
#     #     query.attributes[f"{{{NAMESPACE}}}state"] = str(new_state)
#     #     return query

#     @staticmethod
#     def handle_click_event(
#         root_element: ET._Element, element: ET._Element
#     ) -> QueryEvent:
#         element_id = element.get("id", None)

#         # update query - attributes to be filled out below.
#         query = QueryEvent(
#             *Event.new(),
#             action=QueryEvent.UPDATE,
#             element_id=element_id,
#             attributes=dict(),
#         )

#         if element_id == "warning-light-1":
#             return Matb2.handle_warning_light_1_click(query, element)
#         elif element_id == "warning-light-2":
#             return Matb2.handle_warning_light_2_click(query, element)
#         elif "slider" in element_id:
#             return Matb2.handle_slider_click(query, root_element, element)
#         elif "pump" in element_id:
#             return None  # TODO
#         else:
#             raise ValueError(f"Unrecognised clickable element: {element_id}")

#     # input handlers for the system monitoring task
#     @staticmethod
#     def handle_slider_click(query, root_element, element):
#         # the update query is happening on the box, not the clickable slider
#         query.element_id = f"{SLIDER_BOX}-{query.element_id.split('-')[-1]}"
#         # get the box element from the root element
#         box_element = root_element.xpath(f".//*[@id='{query.element_id}']")[0]
#         box_height = int(box_element.get("height"))
#         inc = box_height / 3
#         inc_steps = int(element.get("height")) / inc
#         nstate = int(inc_steps / 2)  # click resets to the mid point
#         query.attributes["y"] = str(int(element.get("y")) + (nstate - 1) * inc)
#         query.attributes[f"{{{NAMESPACE}}}state"] = str(nstate)
#         return query

#     @staticmethod
#     def handle_warning_light_1_click(query, element):
#         print(element)
#         element_state = element.get(f"{{{NAMESPACE}}}state", None)
#         nstate = 1 - int(element_state)
#         nfill = [GREEN, LIGHTGREY][nstate]
#         query.attributes[f"{{{NAMESPACE}}}state"] = str(nstate)
#         query.attributes["fill"] = nfill  # Default namespace
#         return query

#     @staticmethod
#     def handle_warning_light_2_click(query, element):
#         element_state = element.get(f"{{{NAMESPACE}}}state", None)
#         nstate = 1 - int(element_state)
#         nfill = [LIGHTGREY, RED][nstate]
#         query.attributes[f"{{{NAMESPACE}}}state"] = str(nstate)
#         query.attributes["fill"] = nfill  # Default namespace
#         return query

#     @staticmethod
#     def get_elements(root_element, element_id):
#         return root_element.xpath(f".//*[@id='{element_id}']")
