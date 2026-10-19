from typing import ClassVar

from src.game.core.level import Level
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.heuristic.heuristic_calculator import HeuristicCalculator
from src.solver_algorithms.heuristic.trivial_heuristic_calculator import (
    TrivialHeuristicCalculator,
)


class HeuristicCalculatorFactory:
    _registry: ClassVar[dict[HeuristicCalculatorType, type[HeuristicCalculator]]] = {
        HeuristicCalculatorType.TRIVIAL: TrivialHeuristicCalculator,
    }

    @classmethod
    def create(
        cls, heuristic_calculator_type: HeuristicCalculatorType, level: Level
    ) -> HeuristicCalculator:
        return cls._registry[heuristic_calculator_type](level)
