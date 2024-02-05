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
    <rect id="{WARNING_LIGHT_1}" x="10"  y="10" width="80" height="40" fill="{GREEN}" stroke="black" stroke-width="1" svgre:clickable="true" svgre:state="0"/>
    
    <text x="40"  y="35" fill="#0500d6" stroke="#0500d6">F5</text>
    
    <rect id="{WARNING_LIGHT_2}" x="110" y="10" width="80" height="40" fill="{LIGHTGREY}" stroke="black" stroke-width="1" svgre:clickable="true" svgre:state="0"/>
    <text x="140"  y="35"  fill="#0500d6" stroke="#0500d6">F6</text>

        <!-- Segment dividers for vertical rectangles -->    
        <g id="slider-task" fill="none" stroke="black" stroke-width="1">

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


def stringify_children(node):
    from lxml.etree import tostring
    from itertools import chain

    parts = (
        [node.text]
        + list(
            chain(
                *(
                    [tostring(c, encoding=str, with_tail=False), c.tail]
                    for c in node.getchildren()
                )
            )
        )
        + [node.tail]
    )
    # filter removes possible Nones in texts and tails
    return "".join(filter(None, parts))


from lxml import etree as ET

root = ET.fromstring(MATBII_SVG)

box_element = root.xpath(f".//*[@id='slider-task']")[0]

print(stringify_children(box_element))

print(
    "\n".join(
        text
        for text in [text.strip() for text in box_element.itertext()]
        if len(text) > 0
    )
)

# for inner in [ET.tostring(child, encoding="unicode") for child in box_element]:
#     print("??")
#     print(inner)

# print(root)
