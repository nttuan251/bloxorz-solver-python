from ursina import color, Vec3

# Cấu hình bàn chơi
TILE_SCALE = Vec3(0.95, 0.2, 0.95)
TILE_COLORS = {
    'o': color.gray,
    'S': color.lime,
    'T': color.red
}

# Cấu hình Camera
CAMERA_ORTHOGRAPHIC = True
CAMERA_POS = (8, 12, -12)
CAMERA_ROT = (40, -35, 0)
CAMERA_FOV = 8

# Cấu hình Animation
ROLL_DURATION = 0.15