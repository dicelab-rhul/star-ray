from star_ray.plugin.pygame.view import element_hit_test, find_all_mouse_event_elements
import lxml.etree as ET

SVG = """
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="40" fill="yellow" stroke="black" stroke-width="2" onclick="alert('Circle clicked!');" /> 
</svg>"""

SVG = ET.fromstring(SVG)

mouse_event_elements = find_all_mouse_event_elements(SVG)

for tag, elements in mouse_event_elements.items():
    for element in elements:
        if element_hit_test(element, (10, 10)):
            print("HIT!", ET.tostring(element))
