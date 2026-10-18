from enum import Enum


class CostCalculatorType(str, Enum):
    UNIFORM = "UNIFORM"
    RISK_AWARE = "RISK_AWARE"
