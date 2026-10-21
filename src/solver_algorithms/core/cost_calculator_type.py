from enum import Enum


class CostCalculatorType(str, Enum):
    UNIFORM = "UNIFORM"
    RISK_AWARE = "RISK_AWARE"
    SWITCH_FRIENDLY = "SWITCH_FRIENDLY"
    EFFORT = "EFFORT"
    SPLIT_AWARE = "SPLIT_AWARE"
