#!/usr/bin/env python3
import math
import pyvista as pv

# Configuration constants.
CELL_SPACING = 2.0  # Distance between centers of grid cells.
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

def render_scene(scene, output_file, cell_spacing=CELL_SPACING, shape_size=SHAPE_SIZE):
    """
    Given a 2D array 'scene' (expected to be GRID_SIZE x GRID_SIZE) of shape names,
    this function creates a PyVista Plotter, places each shape at its grid location,
    sets an off-screen camera, and then saves the rendered view to 'output_file'.
    """
    pl = pv.Plotter(off_screen=True, window_size=(1200, 800))
    n = len(scene)  # Expecting n = GRID_SIZE.

    # Place each shape at a location on the x-y plane.
    # (Here we use x for column and y for row. The negative sign for y makes
    # row 0 at the top, similar to array indexing.)
    for row in range(n):
        for col in range(n):
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
    total_width = (n - 1) * cell_spacing
    ground = pv.Plane(center=(total_width/2, -total_width/2, 0),
                      direction=(0, 0, 1),
                      i_size=total_width + cell_spacing,
                      j_size=total_width + cell_spacing)
    pl.add_mesh(ground, color="lightgray", opacity=0.5)

    # Determine a central point for the grid.
    center = (total_width/2, -total_width/2, 0)

    # Set up a camera position at an angle that nicely shows the grid.
    # Here we position the camera by offsetting along x, y, and z.
    cam_pos = (center[0] + n, center[1] - n, n * 1.5)
    pl.camera_position = [cam_pos, center, (0, 0, 1)]

    # Set a white background.
    pl.set_background("white")

    # Render the scene off-screen and save a screenshot.
    pl.show(screenshot=output_file)
    print(f"Scene rendered and saved to {output_file}")

def sample_scene():
    """
    Creates and returns a sample 10x10 scene.
    Empty string '' means no shape in that cell.
    """
    return [
        ["circle", "", "square", "", "triangle", "", "diamond", "", "circle", ""],
        ["square", "circle", "", "triangle", "", "diamond", "", "circle", "", "square"],
        ["", "triangle", "circle", "", "square", "", "diamond", "circle", "triangle", ""],
        ["diamond", "", "triangle", "circle", "", "square", "", "triangle", "circle", "diamond"],
        ["circle", "square", "", "diamond", "triangle", "", "circle", "square", "", "triangle"],
        ["triangle", "", "diamond", "circle", "", "square", "triangle", "", "diamond", "circle"],
        ["", "diamond", "circle", "", "triangle", "square", "", "diamond", "circle", "triangle"],
        ["square", "triangle", "", "diamond", "circle", "", "square", "triangle", "", "diamond"],
        ["diamond", "", "circle", "triangle", "", "diamond", "circle", "", "square", "triangle"],
        ["circle", "diamond", "triangle", "", "circle", "square", "", "diamond", "triangle", "circle"]
    ]

if __name__ == "__main__":
    scene = sample_scene()
    render_scene(scene, "output.png")
