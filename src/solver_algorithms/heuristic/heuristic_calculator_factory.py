from typing import ClassVar

from game.core.level import Level
from solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from solver_algorithms.heuristic.heuristic_calculator import HeuristicCalculator
from solver_algorithms.heuristic.teleport_aware_heuristic_calculator import (
    TeleportAwareHeuristicCalculator,
)
from solver_algorithms.heuristic.trivial_heuristic_calculator import (
    TrivialHeuristicCalculator,
)


class HeuristicCalculatorFactory:
    _registry: ClassVar[dict[HeuristicCalculatorType, type[HeuristicCalculator]]] = {
        HeuristicCalculatorType.TRIVIAL: TrivialHeuristicCalculator,
        HeuristicCalculatorType.TELEPORT_AWARE: TeleportAwareHeuristicCalculator,
    }

    @classmethod
    def create(
        cls, heuristic_calculator_type: HeuristicCalculatorType, level: Level
    ) -> HeuristicCalculator:
        return cls._registry[heuristic_calculator_type](level)
