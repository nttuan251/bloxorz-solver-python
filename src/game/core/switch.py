from enum import Enum


class SwitchActionType(str, Enum):
    TOGGLE = "TOGGLE"
    PERMANENT_CLOSE = "PERMANENT_CLOSE"
    PERMANENT_OPEN = "PERMANENT_OPEN"
    SPLIT = "SPLIT"
