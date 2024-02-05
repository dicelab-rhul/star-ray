import numpy as np

import pygame
import cairosvg

MATB2_XML = """<svg id="root" width="200" height="320" xmlns="http://www.w3.org/2000/svg">
    <!-- Background rectangle -->
    <rect width="200" height="320" fill="lightgrey" />
</svg>"""


# Initialize Pygame
pygame.init()

# must be the same as the svg file
width = 200
height = 320


def surface_to_npim(surface):
    """Transforms a Cairo surface into a numpy array."""
    im = np.frombuffer(surface.get_data(), np.uint8)
    H, W = surface.get_height(), surface.get_width()
    im.shape = (H, W, 4)  # for RGBA
    return im[:, :, :3].transpose(1, 0, 2)


def svg_to_npim(svg_bytestring, dpi=100):
    """Renders a svg bytestring as a RGB image in a numpy array"""
    tree = cairosvg.parser.Tree(bytestring=svg_bytestring)
    surf = cairosvg.surface.PNGSurface(tree, None, dpi).cairo
    return surface_to_npim(surf)


# Create a window of the size of the array
window = pygame.display.set_mode((width, height))

# Create a Pygame surface (same size as the array)
surface = pygame.Surface((width, height))

i = 0
# Main loop
running = True
while running:
    i += 1
    print(i)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw the surface onto the window
    array = svg_to_npim(MATB2_XML)
    print(array.shape)
    # Blit the NumPy array onto the surface
    pygame.surfarray.blit_array(surface, array)
    window.blit(surface, (0, 0))

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
