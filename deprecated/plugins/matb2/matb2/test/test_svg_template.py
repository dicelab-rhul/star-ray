from omegaconf import OmegaConf
from jinja2 import Template
from lxml import etree as ET
import pathlib
import numexpr

from star_ray.event.exitevent import ExitEvent
from star_ray.plugin.pygame import PygameView

path = str(pathlib.Path(__file__).parent.parent)

# this is dangerous, what we want is a simple arthmeic resolver...
OmegaConf.register_new_resolver("eval", numexpr.evaluate)

# Load the YAML configuration file
config = OmegaConf.load(path + "/matb2.yaml")

# Load the SVG template from the file
with open(path + "/matb2.svg", "r") as svg_file:
    svg_template = svg_file.read()

# Create a Jinja template from the SVG template
template = Template(svg_template)

# Render the SVG using the configuration
rendered_svg = template.render(**config)

# Print the rendered SVG
print(rendered_svg)

root = ET.fromstring(rendered_svg)
width, height = int(root.get("width")), int(root.get("height"))
print(width, height)

view = PygameView(width=width, height=height)

while True:
    view.render_svg(rendered_svg)
    events = view.step()
    if any([isinstance(event, ExitEvent) for event in events]):
        view.close()
        break
