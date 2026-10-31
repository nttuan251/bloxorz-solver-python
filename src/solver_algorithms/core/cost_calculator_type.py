from enum import Enum


class CostCalculatorType(str, Enum):
    UNIFORM = "UNIFORM"
    RISK_AWARE = "RISK_AWARE"
    SWITCH_FRIENDLY = "SWITCH_FRIENDLY"
    SPLIT_AWARE = "SPLIT_AWARE"
