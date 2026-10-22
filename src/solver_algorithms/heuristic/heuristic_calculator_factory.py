from typing import ClassVar

from src.game.core.level import Level
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.heuristic.heuristic_calculator import HeuristicCalculator
from src.solver_algorithms.heuristic.grid_distance_heuristic_calculator import (
    GridDistanceHeuristicCalculator,
)
from src.solver_algorithms.heuristic.relaxed_block_heuristic_calculator import (
    RelaxedBlockHeuristicCalculator,
)
from src.solver_algorithms.heuristic.teleport_aware_heuristic_calculator import (
    TeleportAwareHeuristicCalculator,
)
from src.solver_algorithms.heuristic.trivial_heuristic_calculator import (
    TrivialHeuristicCalculator,
)


class HeuristicCalculatorFactory:
    _registry: ClassVar[dict[HeuristicCalculatorType, type[HeuristicCalculator]]] = {
        HeuristicCalculatorType.TRIVIAL: TrivialHeuristicCalculator,
        HeuristicCalculatorType.TELEPORT_AWARE: TeleportAwareHeuristicCalculator,
        HeuristicCalculatorType.GRID_DISTANCE: GridDistanceHeuristicCalculator,
        HeuristicCalculatorType.RELAXED_BLOCK: RelaxedBlockHeuristicCalculator,
    }

    @classmethod
    def create(
        cls, heuristic_calculator_type: HeuristicCalculatorType, level: Level
    ) -> HeuristicCalculator:
        return cls._registry[heuristic_calculator_type](level)
