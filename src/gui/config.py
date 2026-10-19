from ursina import Vec3, color
from ursina.color import rgb

from src.game.core.tile import TileType

TILE_SCALE = Vec3(0.95, 0.2, 0.95)

# Map the new TileType enum to the exact visual properties of the old GUI
TILE_CONFIGS = {
    TileType.START: {
        "color": color.lime,
        "model": "cube",
        "scale": TILE_SCALE,
        "y": -0.1,
    },
    TileType.GOAL: {
        "color": color.white,
        "model": "cube",
        "scale": Vec3(0.95, 0.05, 0.95),
        "y": -0.15,
    },
    TileType.NORMAL: {
        "color": color.gray,
        "model": "cube",
        "scale": TILE_SCALE,
        "y": -0.1,
    },
    TileType.FRAGILE: {
        "color": rgb(231 / 255, 76 / 255, 60 / 255),
        "model": "cube",
        "scale": TILE_SCALE,
        "y": -0.1,
    },
    TileType.BRIDGE: {
        "color": color.azure,
        "model": "cube",
        "scale": TILE_SCALE,
        "y": -0.1,
    },
    TileType.SOFT_SWITCH: {
        "color": color.white,
        "model": "quad",
        "texture": "./assets/Playstation_Circle.png",
        "scale": Vec3(0.7, 0.7, 0.7),
        "rotation": Vec3(90, 0, 0),
        "y": 0.005,
    },
    TileType.HEAVY_SWITCH: {
        "color": color.white,
        "model": "quad",
        "texture": "./assets/Playstation_Cross.png",
        "scale": Vec3(0.7, 0.7, 0.7),
        "rotation": Vec3(90, 0, 0),
        "y": 0.005,
    },
    TileType.SPLIT_SWITCH: {
        "color": color.white,
        "model": "quad",
        "texture": "./assets/Playstation_Triangle.png",
        "scale": Vec3(0.7, 0.7, 0.7),
        "rotation": Vec3(90, 0, 0),
        "y": 0.005,
    },
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
