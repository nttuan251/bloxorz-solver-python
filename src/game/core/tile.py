from enum import Enum


class TileType(str, Enum):
    NORMAL = "NORMAL"
    START = "START"
    GOAL = "GOAL"
    FRAGILE = "FRAGILE"
    SOFT_SWITCH = "SOFT_SWITCH"
    HEAVY_SWITCH = "HEAVY_SWITCH"
    BRIDGE = "BRIDGE"
