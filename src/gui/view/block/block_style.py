"""Visual constants and the pure pose -> 3D transform mapping for the block."""

from __future__ import annotations

from ursina import Vec3, color
from ursina.color import rgb

from src.gui.geometry import Orientation

WHOLE_COLOR = color.orange
ACTIVE_CUBE_COLOR = rgb(29 / 255, 209 / 255, 161 / 255)
INACTIVE_CUBE_COLOR = color.dark_gray

CUBE_Y = 0.45
CUBE_SCALE = Vec3(0.9, 0.9, 0.9)


def transform_for(r: int, c: int, ori: Orientation | str) -> tuple[Vec3, Vec3]:
    """Return (position, scale) of the whole block anchored at tile (r, c)."""
    ori = Orientation(ori)
    if ori is Orientation.STANDING:
        return Vec3(c, 1.0, -r), Vec3(0.9, 2.0, 0.9)
    if ori is Orientation.LYING_H:
        return Vec3(c + 0.5, 0.45, -r), Vec3(1.9, 0.9, 0.9)
    return Vec3(c, 0.45, -(r + 0.5)), Vec3(0.9, 0.9, 1.9)


def cube_position(r: int, c: int) -> Vec3:
    return Vec3(c, CUBE_Y, -r)
