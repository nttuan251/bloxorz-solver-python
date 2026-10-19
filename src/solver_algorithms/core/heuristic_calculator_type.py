from enum import Enum


class HeuristicCalculatorType(str, Enum):
    TRIVIAL = "TRIVIAL"
    TELEPORT_AWARE = "TELEPORT_AWARE"
