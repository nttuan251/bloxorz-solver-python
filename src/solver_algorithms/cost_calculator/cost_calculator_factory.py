from typing import ClassVar

from src.game.core.level import Level
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.cost_calculator.cost_calculator import CostCalculator
from src.solver_algorithms.cost_calculator.uniform_cost_calculator import (
    UniformCostCalculator,
)


class CostCalculatorFactory:
    _registry: ClassVar[dict[CostCalculatorType, type[CostCalculator]]] = {
        CostCalculatorType.UNIFORM: UniformCostCalculator
    }

    @classmethod
    def create(
        cls, cost_calculator_type: CostCalculatorType, level: Level
    ) -> CostCalculator:
        return cls._registry[cost_calculator_type](level)
