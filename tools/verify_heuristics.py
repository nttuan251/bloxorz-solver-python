"""Check every heuristic against every cost function on every level.

For each level the whole reachable state graph is built once with the engine. Then,
for each cost function, the exact optimal cost-to-goal h*(s) of every state is
computed (Dijkstra on the reversed graph) and each heuristic h is checked:

  - admissible:  h(s) <= h*(s)            for every state that can reach the goal
  - consistent:  h(s) <= cost(s, t) + h(t) for every move s -> t
  - optimal:     A* with this cost + heuristic returns a path of cost h*(start)

and the number of nodes A* expands is recorded.

Usage (from the repository root):
    python tools/verify_heuristics.py
    python tools/verify_heuristics.py --maps "maps/level_0*.json" --csv results.csv
"""

import argparse
import csv
import glob
import heapq
import itertools
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.game.core.state import State  # noqa: E402
from src.game.logic.engine import BloxorzGame  # noqa: E402
from src.game.logic.level_loader import LevelLoader  # noqa: E402
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType  # noqa: E402
from src.solver_algorithms.core.heuristic_calculator_type import (  # noqa: E402
    HeuristicCalculatorType,
)
from src.solver_algorithms.core.solver_type import SolverType  # noqa: E402
from src.solver_algorithms.cost_calculator.cost_calculator_factory import (  # noqa: E402
    CostCalculatorFactory,
)
from src.solver_algorithms.heuristic.heuristic_calculator_factory import (  # noqa: E402
    HeuristicCalculatorFactory,
)
from src.solver_algorithms.solvers.solver_factory import SolverFactory  # noqa: E402

EPSILON = 1e-9


@dataclass
class Row:
    level: str
    cost: str
    heuristic: str
    states: int
    optimal_cost: float
    found_cost: float
    expanded: int
    admissibility_violations: int
    consistency_violations: int
    seconds: float

    @property
    def is_optimal(self) -> bool:
        return abs(self.found_cost - self.optimal_cost) < EPSILON


def build_state_graph(game: BloxorzGame) -> tuple[State, list[State], list[tuple[State, State]]]:
    start = game.start_state()
    seen = {start}
    stack = [start]
    edges: list[tuple[State, State]] = []

    while stack:
        state = stack.pop()
        if game.is_goal(state):
            continue
        for _, next_state in game.successors(state):
            edges.append((state, next_state))
            if next_state not in seen:
                seen.add(next_state)
                stack.append(next_state)

    return start, list(seen), edges


def exact_cost_to_goal(
    game: BloxorzGame, states: list[State], edges: list[tuple[State, State, float]]
) -> dict[State, float]:
    reversed_edges: dict[State, list[tuple[State, float]]] = {}
    for state, next_state, cost in edges:
        reversed_edges.setdefault(next_state, []).append((state, cost))

    distances = {state: 0.0 for state in states if game.is_goal(state)}
    counter = itertools.count()
    queue = [(0.0, next(counter), state) for state in distances]
    heapq.heapify(queue)

    while queue:
        distance, _, state = heapq.heappop(queue)
        if distance > distances[state]:
            continue
        for previous_state, cost in reversed_edges.get(state, ()):
            if distance + cost < distances.get(previous_state, math.inf):
                distances[previous_state] = distance + cost
                heapq.heappush(queue, (distance + cost, next(counter), previous_state))

    return distances


def path_cost(game: BloxorzGame, cost_calculator, actions) -> float:
    state, total = game.start_state(), 0.0
    for action in actions:
        next_state = next(s for a, s in game.successors(state) if a == action)
        total += cost_calculator.calculate_cost(state, next_state)
        state = next_state
    assert game.is_goal(state), "solution does not reach the goal"
    return total


def check_level(map_path: str) -> list[Row]:
    level = LevelLoader.parse_level_from_file(map_path)
    game = BloxorzGame(level)
    start, states, moves = build_state_graph(game)
    name = Path(map_path).stem

    heuristic_values = {}
    for heuristic_type in HeuristicCalculatorType:
        heuristic = HeuristicCalculatorFactory.create(heuristic_type, level)
        heuristic_values[heuristic_type] = {s: heuristic.calculate_heuristic(s) for s in states}

    rows = []
    for cost_type in CostCalculatorType:
        cost_calculator = CostCalculatorFactory.create(cost_type, level)
        edges = [(s, t, cost_calculator.calculate_cost(s, t)) for s, t in moves]
        optimal = exact_cost_to_goal(game, states, edges)

        for heuristic_type, h in heuristic_values.items():
            admissibility = sum(1 for s, d in optimal.items() if h[s] > d + EPSILON)
            consistency = sum(1 for s, t, c in edges if h[s] > c + h[t] + EPSILON)

            solver = SolverFactory.create(SolverType.A_STAR, level, cost_type, heuristic_type)
            began = time.perf_counter()
            actions, _ = solver.solve()
            seconds = time.perf_counter() - began

            rows.append(
                Row(
                    level=name,
                    cost=cost_type.name,
                    heuristic=heuristic_type.name,
                    states=len(states),
                    optimal_cost=optimal[start],
                    found_cost=path_cost(game, cost_calculator, actions),
                    expanded=solver.get_expanded_nodes(),
                    admissibility_violations=admissibility,
                    consistency_violations=consistency,
                    seconds=seconds,
                )
            )

    return rows


def print_summary(rows: list[Row]) -> None:
    print()
    print(f"{'cost':16} {'heuristic':15} {'adm.viol':>9} {'cons.viol':>10} "
          f"{'non-optimal maps':>17} {'total expanded':>15}")
    for cost_type in CostCalculatorType:
        for heuristic_type in HeuristicCalculatorType:
            group = [r for r in rows if r.cost == cost_type.name and r.heuristic == heuristic_type.name]
            print(
                f"{cost_type.name:16} {heuristic_type.name:15} "
                f"{sum(r.admissibility_violations for r in group):9} "
                f"{sum(r.consistency_violations for r in group):10} "
                f"{sum(not r.is_optimal for r in group):17} "
                f"{sum(r.expanded for r in group):15}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--maps", default="maps/level_*.json", help="glob of level files")
    parser.add_argument("--csv", help="also write one row per (level, cost, heuristic)")
    args = parser.parse_args()

    rows: list[Row] = []
    for map_path in sorted(glob.glob(args.maps)):
        level_rows = check_level(map_path)
        rows.extend(level_rows)
        bad = [r for r in level_rows if r.admissibility_violations or r.consistency_violations or not r.is_optimal]
        print(f"{Path(map_path).stem}: {level_rows[0].states} states, "
              f"{len(bad)} problem(s): {sorted({f'{r.cost}/{r.heuristic}' for r in bad}) or '-'}")

    print_summary(rows)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["level", "cost", "heuristic", "states", "optimal_cost", "found_cost",
                             "optimal", "expanded", "admissibility_violations",
                             "consistency_violations", "seconds"])
            for r in rows:
                writer.writerow([r.level, r.cost, r.heuristic, r.states, r.optimal_cost, r.found_cost,
                                 r.is_optimal, r.expanded, r.admissibility_violations,
                                 r.consistency_violations, round(r.seconds, 4)])
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
