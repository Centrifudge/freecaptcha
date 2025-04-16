#!/usr/bin/env python3
import math
import pyvista as pv
import noise_adder
import random
from PIL import Image


# Configuration constants.
OUTPUT_FILE = "captcha.png"
RETURN_MODE_SAVE_FILE = 0
RETURN_MODE_HTTP = 1
RETURN_MODE_RETURN = 2
HTTP_ENDPOINT = "localhost:3456"
CELL_SPACING = 1.0  # Distance between centers of grid cells.
SHAPE_SIZE = 1.0    # Size of each 3D shape.
GRID_SIZE = 10      # 10x10 grid.

def get_shape_mesh(shape_name, size=SHAPE_SIZE):
    """
    Returns a PyVista mesh object corresponding to the shape_name.
    The mapping is:
       "circle"  -> Sphere (radius = size/2)
       "square"  -> Cube (with edge length = size)
       "triangle"-> Cone with resolution=3 (triangular base)
       "diamond" -> Octahedron (via PlatonicSolid 'octahedron')
    After creation the mesh is shifted vertically so that its minimum z is 0.
    """
    shape = shape_name.lower()
    if shape == "circle":
        # Create a sphere centered at the origin.
        mesh = pv.Sphere(radius=size/2)
    elif shape == "square":
        # Create a cube centered at the origin.
        mesh = pv.Cube(center=(0, 0, 0), x_length=size, y_length=size, z_length=size)
    elif shape == "triangle":
        # Create a cone with 3 sides (i.e. triangular base).
        # The default cone is centered such that its tip is at the origin.
        # We set direction along +z.
        mesh = pv.Cone(direction=(0, 0, 1), height=size, radius=size/2, resolution=3)
    elif shape == "diamond":
        # Create an octahedron using PyVista's PlatonicSolid.
        mesh = pv.PlatonicSolid('octahedron')
        # Scale the octahedron so that it roughly matches the given size.
        mesh.scale([size/2.0, size/2.0, size/2.0], inplace=True)
    else:
        return None

    # Shift the mesh upward so that its base is at z=0.
    # The bounds are (xmin, xmax, ymin, ymax, zmin, zmax).
    zmin = mesh.bounds[4]
    mesh.translate((0, 0, -zmin), inplace=True)
    return mesh

def render_scene(scene, camera_offset = (0, 0, 0), camera_rotation = (0, 0, 1), cell_spacing=CELL_SPACING, shape_size=SHAPE_SIZE):
    """
    Given a 2D array 'scene' (expected to be GRID_SIZE x GRID_SIZE) of shape names,
    this function creates a PyVista Plotter, places each shape at its grid location,
    sets an off-screen camera, and then saves the rendered view to 'output_file'.
    """
    pl = pv.Plotter(off_screen=True, window_size=(1200, 800))


    # Place each shape at a location on the x-y plane.
    # (Here we use x for column and y for row. The negative sign for y makes
    # row 0 at the top, similar to array indexing.)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            shape_name = scene[row][col]
            if shape_name:
                mesh = get_shape_mesh(shape_name, size=shape_size)
                if mesh is not None:
                    # Compute translation so that each shape is centered in its cell.
                    # The x-coordinate is col*cell_spacing, the y-coordinate is -row*cell_spacing.
                    translation = (col * cell_spacing, -row * cell_spacing, 0)
                    mesh.translate(translation, inplace=True)
                    # Add the mesh to the scene.
                    pl.add_mesh(mesh, color="lightblue", show_edges=True)

    # Optionally, add a ground plane for context.
    total_width = (GRID_SIZE - 1) * cell_spacing
    ground = pv.Plane(center=(total_width/2, -total_width/2, 0),
                      direction=(0, 0, 1),
                      i_size=total_width + cell_spacing,
                      j_size=total_width + cell_spacing)
    pl.add_mesh(ground, color="red", opacity=0.5)

    # Determine a central point for the grid.
    center = (total_width/2, -total_width/2, 0)

    # Set up a camera position at an angle that nicely shows the grid.
    # Here we position the camera by offsetting along x, y, and z.
    cam_pos = (center[0] + GRID_SIZE + camera_offset[0], center[1] - GRID_SIZE + camera_offset[1], GRID_SIZE * 0.5  + camera_offset[2])
    pl.camera_position = [cam_pos, center, camera_rotation]

    # Set a white background.
    pl.set_background("white")

    # Render the scene off-screen and save a screenshot.
    return Image.fromarray(pl.screenshot(return_img = True))
    #pl.show(screenshot=output_file)
    #print(f"Scene rendered and saved to {output_file}")



def generate_captcha(grid_size: int = 10, noise_level: int = 3, return_mode = RETURN_MODE_SAVE_FILE):
    shapes = ["circle", "square", "triangle", "diamond", ""]
    legal_final_corner_shapes = ["circle", "square", "triangle", "diamond"]
    legal_answer_shapes = ["circle", "square", "triangle", "diamond", ""]
    
    global GRID_SIZE
    GRID_SIZE = grid_size

    grid = [["" for x in range(grid_size)] for y in range(grid_size)]

    grid[0][0] = random.choice(legal_answer_shapes)
    grid[0][1] = random.choice(legal_final_corner_shapes)
    grid[1][1] = random.choice(legal_final_corner_shapes)
    grid[1][0] = random.choice(legal_final_corner_shapes)
    
    for i in range(2, grid_size):
        for j in range(grid_size):
            grid[i][j] = random.choice(shapes)
    for i in range(0, 2):
        for j in range(2, grid_size):
            grid[i][j] = random.choice(shapes)
    
    render = render_scene(grid)
    render = noise_adder.add_noise(render)

    if return_mode == RETURN_MODE_RETURN:
        return render
    if return_mode == RETURN_MODE_SAVE_FILE:
        render.save(OUTPUT_FILE)
        return
    else:
        pass


if __name__ == "__main__":
    generate_captcha(9)
