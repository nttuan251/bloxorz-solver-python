import gc
import time
import tracemalloc

from src.game.core.action import Action
from src.game.logic.engine import BloxorzGame
from src.game.logic.level_loader import LevelLoader
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.core.solution_with_metrics import SolutionWithMetrics
from src.solver_algorithms.core.solver_type import SolverType
from src.solver_algorithms.solvers.solver_factory import SolverFactory


class SolverRunner:
    def __init__(
        self,
        solver_type: SolverType,
        map_location: str,
        cost_calculator_type: CostCalculatorType | None = None,
        heuristic_calculator_type: HeuristicCalculatorType | None = None,
    ) -> None:
        self.level = LevelLoader.parse_level_from_file(map_location)
        self.engine = BloxorzGame(self.level)

        if solver_type == SolverType.A_STAR:
            assert (
                heuristic_calculator_type is not None
                and cost_calculator_type is not None
            )

        self.solver = SolverFactory.create(
            solver_type, self.level, cost_calculator_type, heuristic_calculator_type
        )

    def solve(self) -> tuple[list[Action], float]:
        return self.solver.solve()

    def solve_for_metrics(self) -> SolutionWithMetrics:
        gc.collect()
        tracemalloc.start()
        start_time = time.perf_counter()

        solution = self.solve()

        end_time = time.perf_counter()
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        search_time_in_secs = end_time - start_time
        peak_memory_in_mb = peak_memory / (1024**2)
        solution_length = len(
            [action for action in solution[0] if action != Action.SWITCH_CONTROL]
        )
        expanded_notes = self.solver.get_expanded_nodes()

        return SolutionWithMetrics(
            solution,
            search_time_in_secs,
            peak_memory_in_mb,
            expanded_notes,
            solution_length,
        )
