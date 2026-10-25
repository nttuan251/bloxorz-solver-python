from pathlib import Path

from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.core.solution_with_metrics import SolutionWithMetrics
from src.solver_algorithms.core.solver_type import SolverType
from src.solver_algorithms.solver_runner import SolverRunner

SolverParameter = tuple[SolverType, CostCalculatorType, HeuristicCalculatorType]
AggregatedResult = tuple[float, float, float, float]
TestResult = dict[SolverParameter, list[AggregatedResult]]


def load_map_location(map_id: int) -> str:
    map_location = (
        Path(__file__).resolve().parent.parent
        / "maps"
        / f"level_{str(map_id).zfill(2)}.json"
    )

    return str(map_location)


def aggregate_results(
    test_case_results: list[SolutionWithMetrics],
) -> AggregatedResult:
    number_of_cases = len(test_case_results)

    sum_search_time = 0
    sum_peak_memory = 0
    sum_expanded_notes = 0
    sum_solution_length = 0

    for result in test_case_results:
        sum_search_time += result.search_time_in_secs
        sum_peak_memory += result.peak_memory_in_mb
        sum_expanded_notes += result.expanded_notes
        sum_solution_length += result.solution_length

    return (
        sum_search_time / number_of_cases,
        sum_peak_memory / number_of_cases,
        sum_expanded_notes / number_of_cases,
        sum_solution_length / number_of_cases,
    )


def perform_test(
    solver_parameters: list[SolverParameter],
    test_target_groups: list[list[int]],
) -> TestResult:
    """
    Returns the 4 aggregated metrics of each solver for each test group.
    """
    result: dict[
        tuple[SolverType, CostCalculatorType, HeuristicCalculatorType],
        list[tuple[float, float, float, float]],
    ] = {}

    for solver_parameter in solver_parameters:
        result[solver_parameter] = []
        solver_type, cost_calculator_type, heuristic_calculator_type = solver_parameter

        results_of_current_solver: list[SolutionWithMetrics] = []

        for test_target_group in test_target_groups:
            results_of_current_group: list[SolutionWithMetrics] = []

            for test_map_id in test_target_group:
                map_location = load_map_location(test_map_id)

                solver_runner = SolverRunner(
                    solver_type,
                    map_location,
                    cost_calculator_type,
                    heuristic_calculator_type,
                )

                solution_with_metrics = solver_runner.solve_for_metrics()

                results_of_current_group.append(solution_with_metrics)
                results_of_current_solver.append(solution_with_metrics)

            aggregated_result_by_group = aggregate_results(results_of_current_group)
            result[solver_parameter].append(aggregated_result_by_group)

        aggregated_result_total = aggregate_results(results_of_current_solver)
        result[solver_parameter].append(aggregated_result_total)

    return result


def print_result(
    result: TestResult,
    group_names: list[str],
) -> None:
    for (solver, cost, heuristic), group_results in result.items():
        print(
            f"Solver {solver.value}, using {cost.value} cost and {heuristic.value} heuristic:"
        )

        for group_name, (time, memory, expanded, length) in zip(
            group_names, group_results
        ):
            print(
                f"- Result on {group_name}: Mean search time of {time:.6f} seconds, mean peak memory of {memory:.6f} MB, {expanded:.3f} mean expanded notes, {length:.3f} mean solution length"
            )

        print()
