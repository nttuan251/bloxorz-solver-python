# src/gui/config.py
from ursina import color, Vec3

TILE_SCALE = Vec3(0.95, 0.2, 0.95)

TILE_CONFIGS = {
    'S': {'color': color.lime, 'model': 'cube', 'scale': TILE_SCALE, 'y': -0.1},
    'T': {'color': color.dark_gray, 'model': 'cube', 'scale': Vec3(0.95, 0.05, 0.95), 'y': -0.25},
    'o': {'color': color.gray, 'model': 'cube', 'scale': TILE_SCALE, 'y': -0.1},
    '.': {'color': color.gray, 'model': 'cube', 'scale': TILE_SCALE, 'y': -0.1},
    'A': {'color': color.gray, 'model': 'cube', 'scale': TILE_SCALE, 'y': -0.1},
    'B_dest': {'color': color.gray, 'model': 'cube', 'scale': TILE_SCALE, 'y': -0.1},
    'f': {'color': color.orange, 'model': 'cube', 'scale': TILE_SCALE, 'y': -0.1},
    'b': {'color': color.azure, 'model': 'cube', 'scale': TILE_SCALE, 'y': -0.1},

    # Công tắc
    's': {'color': color.white, 'model': 'quad', 'texture': './assets/Playstation_Circle.png', 'scale': Vec3(0.7, 0.7, 0.7), 'rotation': Vec3(90, 0, 0), 'y': 0.005},
    'h': {'color': color.white, 'model': 'quad', 'texture': './assets/Playstation_Cross.png', 'scale': Vec3(0.7, 0.7, 0.7), 'rotation': Vec3(90, 0, 0), 'y': 0.005},
    'p': {'color': color.white, 'model': 'quad', 'texture': './assets/Playstation_Triangle.png', 'scale': Vec3(0.7, 0.7, 0.7), 'rotation': Vec3(90, 0, 0), 'y': 0.005},
}

CAMERA_ORTHOGRAPHIC = True
CAMERA_OFFSET = Vec3(7, 11, -11)
CAMERA_ROT = (40, -35, 0)
CAMERA_FOV = 8
CAMERA_SPEED = 3.0

MIN_FOV = 3.0
MAX_FOV = 18.0
ZOOM_STEP = 1.0
ZOOM_SPEED = 10.0

MOUSE_SENSITIVITY = 120.0
RESET_SPEED = 8.0
ROLL_DURATION = 0.25