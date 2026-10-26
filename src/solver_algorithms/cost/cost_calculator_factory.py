from typing import ClassVar

from src.game.core.level import Level
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.cost.calculators.risk_aware_cost_calculator import (
    RiskAwareCostCalculator,
)
from src.solver_algorithms.cost.calculators.split_aware_cost_calculator import (
    SplitAwareCostCalculator,
)
from src.solver_algorithms.cost.calculators.switch_friendly_cost_calculator import (
    SwitchFriendlyCostCalculator,
)
from src.solver_algorithms.cost.calculators.uniform_cost_calculator import (
    UniformCostCalculator,
)
from src.solver_algorithms.cost.cost_calculator import CostCalculator


class CostCalculatorFactory:
    _registry: ClassVar[dict[CostCalculatorType, type[CostCalculator]]] = {
        CostCalculatorType.UNIFORM: UniformCostCalculator,
        CostCalculatorType.RISK_AWARE: RiskAwareCostCalculator,
        CostCalculatorType.SWITCH_FRIENDLY: SwitchFriendlyCostCalculator,
        CostCalculatorType.SPLIT_AWARE: SplitAwareCostCalculator,
    }

    @classmethod
    def create(
        cls, cost_calculator_type: CostCalculatorType, level: Level
    ) -> CostCalculator:
        return cls._registry[cost_calculator_type](level)
