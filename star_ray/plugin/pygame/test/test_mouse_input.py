from star_ray.event import ExitEvent
from star_ray.plugin.pygame import PygameView
import time

SVG = """
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2"
    onclick="alert('Circle clicked!');" /> 
</svg>"""

view = PygameView(width=100, height=100)

running = True
while running:
    events = view.step()
    for event in events:
        if isinstance(event, ExitEvent):
            running = False
    view.render_svg(SVG)
