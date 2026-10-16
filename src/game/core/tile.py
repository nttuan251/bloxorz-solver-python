from enum import Enum


class TileType(Enum, str):
    NORMAL = "NORMAL"
    START = "START"
    GOAL = "GOAL"
    FRAGILE = "FRAGILE"
