MATBII_SVG = """
<svg id="root" width="200" height="320" xmlns="http://www.w3.org/2000/svg" xmlns:{{svgre}}="{{svgre_namespace}}">
    <!-- Background rectangle -->
    <rect width="200" height="320" fill="{{background_color}}" />

    <g font-family="Arial" font-size="12" >

   
    <rect id="{{warning_light_id}}" x="110" y="10" width="80" height="40" fill="{{background_color}}" stroke="{{stroke_color}}" stroke-width="{{stroke_width}}" {{svgre}}:clickable="true"/>
    <text x="140"  y="35"  fill="#0500d6" stroke="#0500d6">F6</text>

        <!-- Segment dividers for vertical rectangles -->    
        <g fill="none" stroke="black" stroke-width="1">

            {% for j in range(0, 4)  %}
                <!-- Vertical rectangle -->
                <rect id="{{slider}}-{{j}}" x="{{ 10 + j * 50 }}" y="70" width="30" height="220" fill="#add9e6" {{svgre}}:clickable="true"/>
            {% endfor %}
        </g>

    </g>
</svg>
"""

import jinja2

from jinja2 import Environment, meta

# result = jinja2.Template(MATBII_SVG).render()
# print(result)


# Define your template
template_source = """{{a}} + {{b}} - {{c['key']}} {% for j in range(0, 4)  %}
                <!-- Vertical rectangle -->
                <rect id="{{slider}}-{{j}}" x="{{ 10 + j * 50 }}" y="70" width="30" height="220" fill="#add9e6" {{svgre}}:clickable="true"/>
            {% endfor %}"""

# Set up the Jinja2 environment
env = Environment()

# Parse the template
parsed_content = env.parse(template_source)

# Find undeclared variables (i.e., those that are used in the template)
variables = meta.find_undeclared_variables(parsed_content)

print(variables)
