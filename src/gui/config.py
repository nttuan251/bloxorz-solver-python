"""Visual config for the Ursina 3D GUI (agreed palette)."""

from ursina import Vec3, Vec4, color


def _c(r, g, b, a=1.0):
    """Custom shade from 0-255 ints (ursina Color clamps 0-1, so scale here)."""
    return Vec4(r / 255.0, g / 255.0, b / 255.0, a)

# Board tiles — tuned so normal vs special tiles are obvious at a glance.
TILE_SCALE = Vec3(0.95, 0.2, 0.95)
TILE_COLORS = {
    'floor': _c(70, 70, 82),              # dark slate (normal tiles)
    'start': color.lime,                  # green
    'goal': color.red,                    # red hole
    'fragile': _c(255, 130, 0),           # bright orange
    'bridge_open': color.brown,           # brown when open
    'bridge_closed': _c(60, 40, 20, 0.35),# faint ghost when closed
    'soft_base': _c(150, 128, 30),        # dark yellow tint (soft switch)
    'heavy_base': _c(112, 70, 160),       # dark purple tint (heavy switch)
    'split_base': _c(200, 200, 210),      # pale gray (split switch)
    'dest_base': _c(40, 120, 140),        # teal (A/B destinations)
    'void': None,
}
# Switch markers (small props on top of floor tiles)
SWITCH_COLORS = {
    'soft': color.yellow,
    'heavy': color.violet,
    'split': color.white,
    'dest': color.white,
}
# Block / cubes — never white/gray so they can't blend into tiles.
BLOCK_COLOR = _c(40, 130, 255)            # deep blue 1x1x2 block
CUBE_ACTIVE = color.cyan                  # bright cyan = cube being driven
CUBE_IDLE = _c(40, 90, 160)               # dark blue = waiting cube

# Camera — fixed yaw/pitch, follow mode: camera trails the block.
# Offset direction matches CAMERA_ROT so the forward ray stays centered.
CAMERA_ORTHOGRAPHIC = True
CAMERA_ROT = (38, -25, 0)
_CAMERA_YAW_SIN = 0.4226  # sin(25deg)
_CAMERA_YAW_COS = 0.9063  # cos(25deg)

FOLLOW_FOV = 15.0
FOLLOW_T = 12.0
FOLLOW_H = 14.0


def follow_offset():
    from ursina import Vec3 as _V
    return _V(_CAMERA_YAW_SIN * FOLLOW_T, FOLLOW_H, -_CAMERA_YAW_COS * FOLLOW_T)


def camera_for_level(rows, cols):
    """Legacy whole-board framing (kept for reference, not used in follow mode)."""
    cx = (cols - 1) / 2.0
    cz = -(rows - 1) / 2.0
    dist = max(rows, cols)
    t = dist * 0.85 + 7.0
    h = dist * 1.05 + 9.0
    pos = (cx + _CAMERA_YAW_SIN * t, h, cz - _CAMERA_YAW_COS * t)
    fov = max(rows * 0.95, cols / 1.6) + 4.0
    return pos, fov


# Animation
ROLL_DURATION = 0.22
CUBE_DURATION = 0.16
FALL_DURATION = 0.55
REPLAY_DEFAULT_SPEED = 4.0  # moves per second
