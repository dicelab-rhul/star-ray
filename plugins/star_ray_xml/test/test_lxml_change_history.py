from star_ray.plugin.xml import xml_history

NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

XML = """
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Circle 1 -->
        <circle cx="50" cy="50" r="30" fill="red" />
        <!-- Circle 2 -->
        <circle cx="150" cy="50" r="30" fill="green" />
    </g>
        <!-- Rectangle 1 -->
        <rect x="130" y="20" width="50" height="30" fill="orange" />
</svg>
"""
