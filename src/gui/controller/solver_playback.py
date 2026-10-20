from __future__ import annotations

import threading
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ursina import invoke

from src.game.core.action import Action
from src.gui.ui import HUD
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.core.solver_type import SolverType
from src.solver_algorithms.solver_runner import SolverRunner

if TYPE_CHECKING:
    from src.solver_algorithms.solver_runner import SolutionWithMetrics

Callback = Callable[[], None]

SOLVER_TYPES: dict[str, SolverType] = {
    "bfs": SolverType.BFS,
    "dfs": SolverType.DFS,
    "ucs": SolverType.A_STAR,
    "astar": SolverType.A_STAR,
}

_STEP_DELAY = 0.08


@dataclass(frozen=True)
class SolverRequest:
    algo_name: str
    map_path: str
    level_num: int
    cost_type: CostCalculatorType
    heuristic_type: HeuristicCalculatorType

    @property
    def solver_type(self) -> SolverType:
        return SOLVER_TYPES.get(self.algo_name, SolverType.A_STAR)

    @property
    def heuristic(self) -> HeuristicCalculatorType:
        if self.algo_name == "ucs":
            return HeuristicCalculatorType.TRIVIAL
        return self.heuristic_type

    def create_runner(self) -> SolverRunner:
        if self.solver_type is SolverType.A_STAR:
            return SolverRunner(
                self.solver_type,
                self.map_path,
                cost_calculator_type=self.cost_type,
                heuristic_calculator_type=self.heuristic,
            )
        return SolverRunner(self.solver_type, self.map_path)

    def options_line(self) -> str:
        if self.solver_type is not SolverType.A_STAR:
            return ""
        return f"Cost: {self.cost_type.name} | Heuristic: {self.heuristic.name}\n"


class SolverPlayback:
    def __init__(
        self,
        hud: HUD,
        execute_action: Callable[[Action, Callback], None],
        restart: Callable[[Callback], None],
    ) -> None:
        self._hud = hud
        self._execute_action = execute_action
        self._restart = restart
        self.is_playing = False
        self._replay_id = 0

    def cancel(self) -> None:
        self.is_playing = False
        self._replay_id += 1

    def solve_and_play(self, request: SolverRequest) -> None:
        if self.is_playing:
            return

        self._hud.update_stats(f"[{request.algo_name.upper()}] Calculating solution...")
        request_id = self._replay_id

        def worker() -> None:
            metrics = self._run_solver(request)
            invoke(lambda: self._on_solver_finished(request, request_id, metrics))

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _run_solver(request: SolverRequest) -> SolutionWithMetrics | None:
        try:
            return request.create_runner().solve_for_metrics()
        except Exception as exc:
            print(f"\n[ERROR] Solver execution failed: {exc}")
            traceback.print_exc()
            return None

    def _on_solver_finished(
        self,
        request: SolverRequest,
        request_id: int,
        metrics: SolutionWithMetrics | None,
    ) -> None:
        if request_id != self._replay_id:
            return

        if not metrics or not metrics.solution:
            self._hud.update_stats(f"[{request.algo_name.upper()}] No solution found!")
            return

        actions, _cost = metrics.solution

        def start_replay() -> None:
            self._hud.update_stats(
                f"[{request.algo_name.upper()} - LEVEL {request.level_num:02d}]\n"
                f"{request.options_line()}"
                f"Steps: {metrics.solution_length} | Time: {metrics.search_time_in_secs:.4f}s\n"
                f"Expanded: {metrics.expanded_notes} | Peak Mem: {metrics.peak_memory_in_mb:.2f} MB"
            )
            self.is_playing = True
            self._replay_step(actions, 0, self._replay_id)

        self._restart(start_replay)

    def _replay_step(self, actions: list[Action], index: int, replay_id: int) -> None:
        if not self.is_playing or replay_id != self._replay_id:
            return
        if index >= len(actions):
            self.is_playing = False
            return

        def schedule_next() -> None:
            if self.is_playing and replay_id == self._replay_id:
                invoke(
                    lambda: self._replay_step(actions, index + 1, replay_id),
                    delay=_STEP_DELAY,
                )

        self._execute_action(actions[index], schedule_next)
