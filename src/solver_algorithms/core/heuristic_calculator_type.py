from enum import Enum


class HeuristicCalculatorType(str, Enum):
    TRIVIAL = "TRIVIAL"
    TELEPORT_AWARE = "TELEPORT_AWARE"
    GRID_DISTANCE = "GRID_DISTANCE"
    RELAXED_BLOCK = "RELAXED_BLOCK"
