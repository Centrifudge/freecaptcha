from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import random

def add_noise(image, lines = 30, dots = 1500, rotation = 0, blur = 0.6):
    # Load image
    #image = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # 1. Add random lines
    for line in range(lines):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        color = tuple(random.randint(0, 255) for _ in range(3))
        draw.line([start, end], fill=color, width=1)

    # 2. Add random dots
    for dot in range(dots):
        xy = (random.randint(0, width), random.randint(0, height))
        color = tuple(random.randint(0, 255) for _ in range(3))
        draw.point(xy, fill=color)

    # 3. Apply distortion (shear + slight rotation)
    image = image.rotate(random.uniform(-rotation, rotation), resample=Image.BICUBIC, expand=1)

    # 4. Apply filter (blur)
    image = image.filter(ImageFilter.GaussianBlur(radius=blur))

    return image
