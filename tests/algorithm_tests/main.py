from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.core.solver_type import SolverType
from tests.algorithm_tests.util import SolverParameter, perform_test, print_result

GROUP_1 = [1, 2, 3]
GROUP_2 = [4, 5]
GROUP_3 = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
GROUP_4 = [21, 22, 23, 24, 25, 26, 27, 28]
GROUP_5 = [29, 30, 31, 32, 33]

ALL_GROUPS = [GROUP_1, GROUP_2, GROUP_3, GROUP_4, GROUP_5]

CHOSEN_HEURISTIC = HeuristicCalculatorType.RELAXED_BLOCK


def test_baseline_algorithms_on_all_groups() -> None:
    solver_parameters: list[SolverParameter] = [
        (SolverType.BFS, CostCalculatorType.UNIFORM, HeuristicCalculatorType.TRIVIAL),
        (SolverType.DFS, CostCalculatorType.UNIFORM, HeuristicCalculatorType.TRIVIAL),
        (
            SolverType.A_STAR,
            CostCalculatorType.UNIFORM,
            HeuristicCalculatorType.TRIVIAL,
        ),
        (
            SolverType.A_STAR,
            CostCalculatorType.UNIFORM,
            HeuristicCalculatorType.GRID_DISTANCE,
        ),
    ]

    test_result = perform_test(solver_parameters, ALL_GROUPS)
    print_result(
        test_result,
        ["Group 1", "Group 2", "Group 3", "Group 4", "Group 5", "all tested Groups"],
    )


def test_heuristic_comparison_on_all_groups() -> None:
    solver_parameters: list[SolverParameter] = [
        (
            SolverType.A_STAR,
            CostCalculatorType.UNIFORM,
            HeuristicCalculatorType.TRIVIAL,
        ),
        (
            SolverType.A_STAR,
            CostCalculatorType.UNIFORM,
            HeuristicCalculatorType.TELEPORT_AWARE,
        ),
        (
            SolverType.A_STAR,
            CostCalculatorType.UNIFORM,
            HeuristicCalculatorType.GRID_DISTANCE,
        ),
        (
            SolverType.A_STAR,
            CostCalculatorType.UNIFORM,
            HeuristicCalculatorType.RELAXED_BLOCK,
        ),
    ]

    test_result = perform_test(solver_parameters, ALL_GROUPS)
    print_result(
        test_result,
        ["Group 1", "Group 2", "Group 3", "Group 4", "Group 5", "all tested Groups"],
    )


def test_cost_comparison_on_all_groups() -> None:
    solver_parameters: list[SolverParameter] = [
        (SolverType.A_STAR, CostCalculatorType.UNIFORM, CHOSEN_HEURISTIC),
        (SolverType.A_STAR, CostCalculatorType.RISK_AWARE, CHOSEN_HEURISTIC),
        (SolverType.A_STAR, CostCalculatorType.SPLIT_AWARE, CHOSEN_HEURISTIC),
        (SolverType.A_STAR, CostCalculatorType.SWITCH_FRIENDLY, CHOSEN_HEURISTIC),
    ]

    test_result = perform_test(solver_parameters, ALL_GROUPS)
    print_result(
        test_result,
        ["Group 1", "Group 2", "Group 3", "Group 4", "Group 5", "all tested Groups"],
    )


if __name__ == "__main__":
    # test_baseline_algorithms_on_all_groups()
    # test_heuristic_comparison_on_all_groups()
    test_cost_comparison_on_all_groups()
