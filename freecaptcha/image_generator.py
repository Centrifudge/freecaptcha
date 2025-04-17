import math
import pyvista as pv
import freecaptcha.noise_adder as noise_adder
import random
from PIL import Image


OUTPUT_FILE = r"captcha_{solution}.png"
RETURN_MODE_SAVE_FILE = 0
# RETURN_MODE_HTTP = 1
RETURN_MODE_RETURN = 2
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
    pl = pv.Plotter(off_screen=True, window_size=(300, 200))

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
    cam_pos = (center[0] + GRID_SIZE + camera_offset[0], center[1] - GRID_SIZE + camera_offset[1], GRID_SIZE * 0.6  + camera_offset[2])
    pl.camera_position = [cam_pos, center, camera_rotation]

    # Set a white background.
    pl.set_background("white")

    # Render the scene off-screen and return it
    return Image.fromarray(pl.screenshot(return_img = True))



def generate_captcha(grid_size: int = 10, noise_level: int = 3, return_mode = RETURN_MODE_SAVE_FILE):
    shapes = ["circle", "square", "triangle", "diamond", ""]
    legal_final_corner_shapes = ["circle", "square", "triangle", "diamond"]
    legal_answer_shapes = ["circle", "square", "triangle", "diamond"]
    
    global GRID_SIZE
    GRID_SIZE = grid_size

    grid = [["" for x in range(grid_size)] for y in range(grid_size)]

    solution = grid[0][0] = random.choice(legal_answer_shapes)
    grid[0][1] = random.choice(legal_final_corner_shapes)
    grid[1][1] = random.choice(legal_final_corner_shapes)
    grid[1][0] = random.choice(legal_final_corner_shapes)
    
    for i in range(2, grid_size):
        for j in range(grid_size):
            grid[i][j] = random.choice(shapes)
    for i in range(0, 2):
        for j in range(2, grid_size):
            grid[i][j] = random.choice(shapes)
    if noise_level > 0:
        render = render_scene(grid, camera_rotation = (random.choice((-1, 1)) * noise_level / 5, 0, 1))
        noise_args = [10 * noise_level, 500 * noise_level, noise_level, noise_level / 5]
        render = noise_adder.add_noise(render, *noise_args)
    else:
        render = render_scene(grid)

    if return_mode == RETURN_MODE_RETURN:
        return render, solution
    if return_mode == RETURN_MODE_SAVE_FILE:
        render.save(OUTPUT_FILE.replace(r"{solution}", solution))
        return
    return


if __name__ == "__main__":
    generate_captcha(10, 3)
