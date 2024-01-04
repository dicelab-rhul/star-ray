from abc import abstractmethod
from typing import List
from blinker import signal
from lxml import (
    etree as ET,
)  # parse the svg oobservation so that actions may be taken on it

from svgrenderengine.engine import SVGApplication, find_all_clickable_elements_at
from svgrenderengine.pygame import PygameView
from svgrenderengine.event import (
    Event,
    QueryEvent,
    MouseMotionEvent,
    MouseButtonEvent,
    KeyEvent,
    ExitEvent,
)
from ...utils.logging import LOGGER
from ...agent import Agent

NAMESPACE = "svg_render_engine"
GREEN = "#95d540"
RED = "#e6584f"
LIGHTGREY = "#f5f5f5"

WARNING_LIGHT_1 = "warning-light-1"
WARNING_LIGHT_2 = "warning-light-2"
SLIDER = "slider"
SLIDER_BOX = "slider-box"

MATBII_SVG = f"""
<svg id="root" width="200" height="320" xmlns="http://www.w3.org/2000/svg" xmlns:svgre="{NAMESPACE}">
    <!-- Background rectangle -->
    <rect width="200" height="320" fill="{LIGHTGREY}" />

    <g font-family="Arial" font-size="12" >

    <!-- Top rectangles -->
    <rect id="{WARNING_LIGHT_1}" x="10"  y="10" width="80" height="40" fill="{GREEN}" stroke="black" stroke-width="1" svgre:state="0" svgre:clickable="true"/>
    <text x="40"  y="35" fill="#0500d6" stroke="#0500d6">F5</text>
    
    <rect id="{WARNING_LIGHT_2}" x="110" y="10" width="80" height="40" fill="{LIGHTGREY}" stroke="black" stroke-width="1" svgre:state="0" svgre:clickable="true"/>
    <text x="140"  y="35"  fill="#0500d6" stroke="#0500d6">F6</text>

        <!-- Segment dividers for vertical rectangles -->    
        <g fill="none" stroke="black" stroke-width="1">

            {{% for j in range(0, 4)  %}}
                <!-- Vertical rectangle -->
                <rect id="{SLIDER}-{{{{j}}}}" x="{{{{ 10 + j * 50 }}}}" y="70" width="30" height="220" fill="#add9e6" svgre:clickable="true"/>

                <!-- Moveable rect for Vertical rectangle-->
                <rect id="{SLIDER_BOX}-{{{{j}}}}" x="{{{{ 10 + j * 50 }}}}" y="150" width="30" height="60" stroke="#4683b2" fill="#4683b2" svgre:state="{{{{150 / 30}}}}"/>

                <!-- Dividers for Vertical rectangle -->
                {{% for i in range(1, 12) %}}
                <rect x="{{{{ 10 + j * 50 }}}}" y="{{{{ 50 + i * 20 }}}}" width="30" height="20"/>
                {{% endfor %}}
                
                <!-- Bottom text for Vertical rectangle -->
                <text x="{{{{ 10 + j * 50 }}}}" y="310"  fill="#0500d6" stroke="#0500d6">F{{{{j + 1}}}}</text>
            {{% endfor %}}
        </g>

    </g>
</svg>
"""


class Matb2(SVGApplication):
    def __init__(self):
        super().__init__(svg_code=MATBII_SVG)

    @staticmethod
    def get_elements(root_element, element_id):
        return root_element.xpath(f".//*[@id='{element_id}']")

    @staticmethod
    def update_slider_state(root_element, element, new_state):
        element_id = element.get("id")
        # trying to update an element that is not a slider?
        assert "slider" in element_id
        query = QueryEvent(
            *Event.new(),
            action=QueryEvent.UPDATE,
            element_id=element_id,
            attributes=dict(),
        )
        # the update query is happening on the box, not the clickable slider
        query.element_id = f"{SLIDER_BOX}-{query.element_id.split('-')[-1]}"
        # get the box element from the root element
        box_element = root_element.xpath(f".//*[@id='{query.element_id}']")[0]
        box_height = int(box_element.get("height"))
        inc = box_height / 3
        inc_steps = int(element.get("height")) / inc  # total number of steps...
        new_state = max(min(new_state, inc_steps - 1), 1)  # clamp the new state...
        query.attributes["y"] = str(int(element.get("y")) + (new_state - 1) * inc)
        query.attributes[f"{{{NAMESPACE}}}state"] = str(new_state)
        return query

    @staticmethod
    def handle_click_event(
        root_element: ET._Element, element: ET._Element
    ) -> QueryEvent:
        element_id = element.get("id", None)

        # update query - attributes to be filled out below.
        query = QueryEvent(
            *Event.new(),
            action=QueryEvent.UPDATE,
            element_id=element_id,
            attributes=dict(),
        )

        if element_id == "warning-light-1":
            return Matb2.handle_warning_light_1_click(query, element)
        elif element_id == "warning-light-2":
            return Matb2.handle_warning_light_2_click(query, element)
        elif "slider" in element_id:
            return Matb2.handle_slider_click(query, root_element, element)
        elif "pump" in element_id:
            return None  # TODO
        else:
            raise ValueError(f"Unrecognised clickable element: {element_id}")

    # input handlers for the system monitoring task
    @staticmethod
    def handle_slider_click(query, root_element, element):
        # the update query is happening on the box, not the clickable slider
        query.element_id = f"{SLIDER_BOX}-{query.element_id.split('-')[-1]}"
        # get the box element from the root element
        box_element = root_element.xpath(f".//*[@id='{query.element_id}']")[0]
        box_height = int(box_element.get("height"))
        inc = box_height / 3
        inc_steps = int(element.get("height")) / inc
        nstate = int(inc_steps / 2)  # click resets to the mid point
        query.attributes["y"] = str(int(element.get("y")) + (nstate - 1) * inc)
        query.attributes[f"{{{NAMESPACE}}}state"] = str(nstate)
        return query

    @staticmethod
    def handle_warning_light_1_click(query, element):
        element_state = element.get(f"{{{NAMESPACE}}}state", None)
        nstate = 1 - int(element_state)
        nfill = [GREEN, LIGHTGREY][nstate]
        query.attributes[f"{{{NAMESPACE}}}state"] = str(nstate)
        query.attributes["fill"] = nfill  # Default namespace
        return query

    @staticmethod
    def handle_warning_light_2_click(query, element):
        element_state = element.get(f"{{{NAMESPACE}}}state", None)
        nstate = 1 - int(element_state)
        nfill = [LIGHTGREY, RED][nstate]
        query.attributes[f"{{{NAMESPACE}}}state"] = str(nstate)
        query.attributes["fill"] = nfill  # Default namespace
        return query


class Matb2AgentBase(Agent):
    """Base class for agents that are able to interact with the matb2 application."""

    def __init__(self):
        super().__init__()
        self._svg_root = None
        self._actions = []  # the actions to execute after each call to cycle
        self._execute_signal = signal("execute")

    def sense(self):
        perceive_action = QueryEvent(
            *Event.new(),
            QueryEvent.SELECT,
            "root",
            ["width", "height", "_xml"],  # get all xml data for rendering
        )
        self._execute_signal.send(self.id, action=perceive_action)

    def execute(self):
        # execute all actions that were decided upon
        self._execute_signal.send(self.id, actions=self._actions)
        self._actions.clear()  # clear ready for next cycle

    @abstractmethod
    def cycle(self, perceptions):
        pass  # this will be implemented by a subclass. See Matb2Agent and Matb2Avatar.


class Matb2Agent(Matb2AgentBase):
    """This agent manages all of the events in the MATB2 system. It will read a schedule file and produce QueryEvent updates to change the interface accordingly."""

    def __init__(self):
        super().__init__()
        self._step = 0

    def cycle(self, perceptions):
        self.perceive(perceptions)
        self.decide()
        self._step += 1

    def decide(self):
        if self._step == 0:
            query = Matb2.update_slider_state(
                self._svg_root, Matb2.get_elements(self._svg_root, "slider-1")[0], 0
            )
            self._actions = [query]

    def perceive(self, perceptions):
        for percept in perceptions:
            if "_xml" in percept.data:
                svg_code = percept.data["_xml"]
                self._svg_root = ET.fromstring(svg_code)
            else:
                # these are the ResponseEvents of actions that have been taken by the user
                print("reponse: ", percept)


class Matb2Avatar(Matb2AgentBase):
    """A special kind of agent that represents the user. It is responisble for gathering user input and rendering the state of the given application."""

    def __init__(self):
        super().__init__()
        self._view = None
        self._mouse_pressed_on = []
        self._key_pressed_on = []

    def cycle(self, perceptions):
        self.perceive(perceptions)
        self.decide()

    def perceive(self, perceptions):
        # print(perceptions)
        for percept in perceptions:
            if "_xml" in percept.data:
                if self._view:
                    self._render(percept)
                else:  # a new view should be created
                    self._view = PygameView(
                        width=percept.data["width"], height=percept.data["height"]
                    )
                    self._render(percept)
            else:
                # these are the ResponseEvents of actions that have been taken by the user
                print("reponse: ", percept)

    def decide(self):
        # get the users actions from the view
        for event in self._view.step():
            LOGGER.log_event(event)
            if isinstance(event, MouseMotionEvent):
                actions = self.handle_mouse_motion_event(event)
            elif isinstance(event, MouseButtonEvent):
                actions = self.handle_mouse_button_event(event)
            elif isinstance(event, KeyError):
                actions = self.handle_keyboard_event(event)
            elif isinstance(event, ExitEvent):
                actions = self.handle_exit_event(event)
            else:
                raise ValueError(f"Unknown event {event} produced by {self._view}")
            self._actions.extend(actions)

    def handle_mouse_motion_event(self, event) -> List[QueryEvent]:
        # NOTE: 'relative=(0,0)' indicates that the mouse moved into the window.
        return []  # nothing to do except log the event

    def handle_mouse_button_event(self, event) -> List[QueryEvent]:
        # handle button clicks for each of the parts of the MATBII interface
        actions = []
        clickable_elements = find_all_clickable_elements_at(
            self._svg_root, event.position
        )
        if event.status == "pressed":
            assert len(self._mouse_pressed_on) == 0
            for element in clickable_elements:
                element_id = element.get("id", None)
                self._mouse_pressed_on.append(element_id)
        elif event.status == "released":
            for element in clickable_elements:
                element_id = element.get("id", None)
                if element_id in self._mouse_pressed_on:
                    action = Matb2.handle_click_event(self._svg_root, element)
                    if action:
                        actions.append(action)
            self._mouse_pressed_on.clear()
        return actions

    def handle_keyboard_event(self, event) -> List[QueryEvent]:
        return []

    def handle_exit_event(self, event) -> List[QueryEvent]:
        self._view.close()  # TODO destroy this agent aswell? perhaps an action needs to be taken here...
        return []

    def _render(self, percept):
        # TODO check if the width/height have changed...
        svg_code = percept.data["_xml"]
        self._view.render_svg(svg_code)
        # this might be a little slow to do on every cycle, but its fine for a prototype
        self._svg_root = ET.fromstring(svg_code)
