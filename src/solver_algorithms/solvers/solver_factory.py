from typing import ClassVar

from src.game.core.level import Level
from src.game.logic.engine import BloxorzGame
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.core.solver_type import SolverType
from src.solver_algorithms.solvers.a_star import AStarSolver
from src.solver_algorithms.solvers.BFS import BFSSolver
from src.solver_algorithms.solvers.DFS import DFSSolver
from src.solver_algorithms.solvers.solver import Solver


class SolverFactory:
    _registry: ClassVar[dict[SolverType, type[Solver]]] = {
        SolverType.BFS: BFSSolver,
        SolverType.DFS: DFSSolver,
        SolverType.A_STAR: AStarSolver,
    }

    @classmethod
    def create(
        cls,
        solver_type: SolverType,
        level: Level,
        cost_calculator_type: CostCalculatorType | None = None,
        heuristic_calculator_type: HeuristicCalculatorType | None = None,
    ) -> Solver:
        engine = BloxorzGame(level)

        if solver_type == SolverType.A_STAR:
            assert (
                heuristic_calculator_type is not None
                and cost_calculator_type is not None
            )

        return cls._registry[solver_type](
            engine,
            level,
            cost_calculator_type,
            heuristic_calculator_type,
        )
