from pathlib import Path

from src.solver_algorithms.core.solver_type import SolverType
from src.solver_algorithms.solver_runner import SolverRunner

if __name__ == "__main__":
    file_location = Path(__file__).resolve().parent.parent / "maps" / "level_01.json"

    solver_runner = SolverRunner(
        solver_type=SolverType.DFS,
        map_location=str(file_location),
        cost_calculator_type=None,
        heuristic_calculator_type=None,
    )

    result = solver_runner.solve()
    result_with_metrics = solver_runner.solve_for_metrics()
