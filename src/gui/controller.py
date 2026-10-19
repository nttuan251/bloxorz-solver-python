"""Game controller: glue between the Bloxorz engine/solver and the Ursina GUI.

Design rules
------------
* The engine is the single source of truth. The controller never simulates
  moves on its own: it asks ``BloxorzGame.successors`` for the legal next
  states, and any action that is not among them is animated as a failure.
* The GUI only *renders* what the engine decided. The one piece of GUI-side
  bookkeeping is ``_cube_slots``: which cube *sprite* (slot 1 or 2) currently
  sits on which tile. The engine stores split cubes as an unordered pair that
  can swap order between states, so sprite identity must never be derived from
  "first/second coords".
"""

from __future__ import annotations

import threading
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from ursina import Entity, Vec3, camera, held_keys, invoke, lerp, mouse, time

import src.gui.config as config
from src.game.core.action import Action
from src.game.logic.engine import BloxorzGame
from src.game.logic.level_loader import LevelLoader
from src.gui.block import Block
from src.gui.board import Board
from src.gui.ui import HUD
from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType
from src.solver_algorithms.core.solver_type import SolverType
from src.solver_algorithms.solver_runner import SolverRunner

if TYPE_CHECKING:
    # Adjust these two paths to wherever Level / State live in your project.
    from src.game.core.level import Level
    from src.game.core.state import State

Coordinate = tuple[int, int]
Vec3Tuple = tuple[float, float, float]
Callback = Callable[[], None]


# --------------------------------------------------------------------------- #
# Pure geometry helpers (no GUI, no engine state)
# --------------------------------------------------------------------------- #


class Orientation(str, Enum):
    """Values match the strings the Block animations already expect."""

    STANDING = "STANDING"
    LYING_H = "LYING_H"
    LYING_V = "LYING_V"


@dataclass(frozen=True)
class BlockPose:
    """Where a whole block sits, anchored at its top-left occupied tile."""

    row: int
    col: int
    orientation: Orientation

    @classmethod
    def from_state(cls, state: State) -> BlockPose:
        r1, c1 = state.get_first_coords()
        r2, c2 = state.get_second_coords()
        if state.is_lying_horizontally():
            return cls(r1, min(c1, c2), Orientation.LYING_H)
        if state.is_lying_vertically():
            return cls(min(r1, r2), c1, Orientation.LYING_V)
        return cls(r1, c1, Orientation.STANDING)

    def after(self, action: Action) -> BlockPose:
        d_row, d_col, orientation = _POSE_TRANSITIONS[self.orientation][action]
        return BlockPose(self.row + d_row, self.col + d_col, orientation)

    def roll_pivot(self, action: Action) -> tuple[Vec3Tuple, Vec3Tuple]:
        """Return (pivot position, rotation axis) for rolling in ``action``."""
        r, c = self.row, self.col
        if self.orientation is Orientation.STANDING:
            table = {
                Action.RIGHT: ((c + 0.5, 0, -r), (0, 0, 90)),
                Action.LEFT: ((c - 0.5, 0, -r), (0, 0, -90)),
                Action.UP: ((c, 0, -r + 0.5), (90, 0, 0)),
                Action.DOWN: ((c, 0, -r - 0.5), (-90, 0, 0)),
            }
        elif self.orientation is Orientation.LYING_H:
            table = {
                Action.RIGHT: ((c + 1.5, 0, -r), (0, 0, 90)),
                Action.LEFT: ((c - 0.5, 0, -r), (0, 0, -90)),
                Action.UP: ((c + 0.5, 0, -r + 0.5), (90, 0, 0)),
                Action.DOWN: ((c + 0.5, 0, -r - 0.5), (-90, 0, 0)),
            }
        else:
            table = {
                Action.RIGHT: ((c + 0.5, 0, -(r + 0.5)), (0, 0, 90)),
                Action.LEFT: ((c - 0.5, 0, -(r + 0.5)), (0, 0, -90)),
                Action.UP: ((c, 0, -r + 0.5), (90, 0, 0)),
                Action.DOWN: ((c, 0, -(r + 1.5)), (-90, 0, 0)),
            }
        return table[action]


# (row offset, col offset, resulting orientation) of the anchor tile per action.
_POSE_TRANSITIONS: dict[Orientation, dict[Action, tuple[int, int, Orientation]]] = {
    Orientation.STANDING: {
        Action.RIGHT: (0, 1, Orientation.LYING_H),
        Action.LEFT: (0, -2, Orientation.LYING_H),
        Action.UP: (-2, 0, Orientation.LYING_V),
        Action.DOWN: (1, 0, Orientation.LYING_V),
    },
    Orientation.LYING_H: {
        Action.RIGHT: (0, 2, Orientation.STANDING),
        Action.LEFT: (0, -1, Orientation.STANDING),
        Action.UP: (-1, 0, Orientation.LYING_H),
        Action.DOWN: (1, 0, Orientation.LYING_H),
    },
    Orientation.LYING_V: {
        Action.RIGHT: (0, 1, Orientation.LYING_V),
        Action.LEFT: (0, -1, Orientation.LYING_V),
        Action.UP: (-1, 0, Orientation.STANDING),
        Action.DOWN: (2, 0, Orientation.STANDING),
    },
}

_DIRECTION_DELTAS: dict[Action, Coordinate] = {
    Action.UP: (-1, 0),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
    Action.RIGHT: (0, 1),
}

_KEY_BINDINGS: dict[str, Action] = {
    "right arrow": Action.RIGHT,
    "left arrow": Action.LEFT,
    "up arrow": Action.UP,
    "down arrow": Action.DOWN,
    "space": Action.SWITCH_CONTROL,
}

_SOLVER_TYPES: dict[str, SolverType] = {
    "bfs": SolverType.BFS,
    "dfs": SolverType.DFS,
    "ucs": SolverType.A_STAR,
    "astar": SolverType.A_STAR,
}

_AUTOPLAY_STEP_DELAY = 0.08


# --------------------------------------------------------------------------- #
# Controller
# --------------------------------------------------------------------------- #


class GameController:
    """Coordinates input, engine, solver playback, camera and HUD."""

    def __init__(self, max_levels: int = 33) -> None:
        self.max_levels = max_levels
        self.current_level_num = 1
        self.manual_moves = 0
        self.is_auto_playing = False
        self._replay_id = 0  # bumped whenever a running replay must be cancelled

        self.level: Level
        self.game: BloxorzGame
        self.state: State
        self.board: Board
        self.block: Block

        # Sprite slot (1 or 2) -> tile it currently occupies. Only meaningful
        # while the block is split.
        self._cube_slots: dict[int, Coordinate] = {}

        self.target_fov: float = config.CAMERA_FOV

        self.hud = HUD(
            on_solve_click=self.solve_and_play,
            on_manual_click=self.switch_to_manual,
            on_level_change=self.change_level,
            on_select_level=self.select_stage_direct,
            on_restart_click=lambda: self.restart_with_fly_up(update_hud=True),
            max_levels=self.max_levels,
        )

        self._setup_camera()
        self.load_stage(self.current_level_num, initial=True)

    # ------------------------------------------------------------------ #
    # Camera / per-frame update / input
    # ------------------------------------------------------------------ #

    def _setup_camera(self) -> None:
        self.cam_pivot = Entity()
        camera.orthographic = config.CAMERA_ORTHOGRAPHIC
        camera.parent = self.cam_pivot
        camera.position = config.CAMERA_OFFSET
        camera.rotation = config.CAMERA_ROT
        camera.fov = config.CAMERA_FOV

    def update(self) -> None:
        if not getattr(self, "block", None):
            return

        active_cube = self.block.get_active_cube()
        if active_cube:
            target = Vec3(active_cube.world_x, 0, active_cube.world_z)
            self.cam_pivot.position = lerp(
                self.cam_pivot.position, target, time.dt * config.CAMERA_SPEED
            )

        if held_keys["left mouse"]:
            self.cam_pivot.rotation_y += mouse.velocity[0] * config.MOUSE_SENSITIVITY
            self.cam_pivot.rotation_x -= mouse.velocity[1] * config.MOUSE_SENSITIVITY
        else:
            self.cam_pivot.rotation = lerp(
                self.cam_pivot.rotation, Vec3(0, 0, 0), time.dt * config.RESET_SPEED
            )

        camera.fov = lerp(camera.fov, self.target_fov, time.dt * config.ZOOM_SPEED)

    def handle_input(self, key: str) -> None:
        if key == "scroll up":
            self.target_fov = max(config.MIN_FOV, self.target_fov - config.ZOOM_STEP)
            return
        if key == "scroll down":
            # NOTE: the old code added ZOOM_SPEED here (copy/paste bug).
            self.target_fov = min(config.MAX_FOV, self.target_fov + config.ZOOM_STEP)
            return

        if self.is_auto_playing:
            return

        if key in _KEY_BINDINGS:
            self.handle_action(_KEY_BINDINGS[key])
        elif key == "r":
            self.restart_with_fly_up(update_hud=True)

    # ------------------------------------------------------------------ #
    # Level lifecycle
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_map_path(level_num: int) -> str:
        """Single source of truth for map paths (used by loader and solver)."""
        json_path = f"maps/level_{level_num:02d}.json"
        if Path(json_path).exists():
            return json_path
        return f"maps/level_{level_num:02d}.txt"

    def load_stage(self, level_num: int, initial: bool = False) -> None:
        self.current_level_num = level_num
        self._cancel_replay()
        self.manual_moves = 0

        if (
            not initial
            and getattr(self, "board", None)
            and getattr(self, "block", None)
        ):
            self.block.animate_exit_fly_up(duration=0.4)
            self.board.animate_exit_fall_down(
                pause_duration=0.35, on_complete=lambda: self._build_stage(level_num)
            )
        else:
            self._build_stage(level_num)

    def _build_stage(self, level_num: int) -> None:
        if getattr(self, "board", None):
            self.board.destroy_board()
        if getattr(self, "block", None):
            self.block.destroy_block()

        self.level = LevelLoader.parse_level_from_file(self._get_map_path(level_num))
        self.game = BloxorzGame(self.level)
        self.state = self.game.start_state()
        self._cube_slots.clear()

        start_row, start_col = self.level.get_start()
        self.board = Board(self.level, animate_entrance=True, start_delay=0.3)
        self.board.sync_bridges(
            self.state.get_bridges_open_states(), animate_entrance=True
        )
        self.block = Block(start_row, start_col)
        self.block.animate_drop_in(
            start_row, start_col, delay=self.board.get_entrance_duration()
        )

        self.cam_pivot.position = self.block.entity.world_position
        self.hud.update_level_display(level_num)
        self._show_manual_stats()

    def change_level(self, delta: int) -> None:
        target = max(1, min(self.max_levels, self.current_level_num + delta))
        if target != self.current_level_num:
            self.load_stage(target)

    def select_stage_direct(self, level_num: int) -> None:
        if level_num != self.current_level_num:
            self.load_stage(level_num)

    def switch_to_manual(self) -> None:
        if not self.is_auto_playing:
            self.restart_with_fly_up(update_hud=True)

    def reset_game(
        self,
        drop_in: bool = False,
        on_complete: Callback | None = None,
        update_hud: bool = True,
    ) -> None:
        self._cancel_replay()
        self.manual_moves = 0
        if update_hud:
            self._show_manual_stats()

        self.state = self.game.start_state()
        self._cube_slots.clear()
        start_row, start_col = self.level.get_start()

        self.board.sync_bridges(self.state.get_bridges_open_states())
        self.board.reset(animate_entrance=False)
        self.block.cleanup_split()

        if drop_in:
            self.block.animate_drop_in(
                start_row, start_col, delay=0.0, on_complete=on_complete
            )
        else:
            self.block.is_animating = False
            self.block.set_transform(start_row, start_col, Orientation.STANDING.value)

    def restart_with_fly_up(
        self, on_complete: Callback | None = None, update_hud: bool = True
    ) -> None:
        self.is_auto_playing = False
        self.board.sync_bridges(self.game.start_state().get_bridges_open_states())

        def reset_with_drop_in() -> None:
            self.reset_game(
                drop_in=True, on_complete=on_complete, update_hud=update_hud
            )

        if self._block_is_visible():
            self.block.animate_exit_fly_up(
                duration=0.35, on_complete=reset_with_drop_in
            )
        else:
            reset_with_drop_in()

    def _block_is_visible(self) -> bool:
        entity = getattr(self.block, "entity", None)
        return bool(entity and entity.enabled and not self.game.is_goal(self.state))

    def _cancel_replay(self) -> None:
        self.is_auto_playing = False
        self._replay_id += 1

    def _show_manual_stats(self) -> None:
        self.hud.update_stats(
            f"[LEVEL {self.current_level_num:02d} - MANUAL MODE]\nMoves: {self.manual_moves}"
        )

    def _count_manual_move(self) -> None:
        if not self.is_auto_playing:
            self.manual_moves += 1
            self._show_manual_stats()

    # ------------------------------------------------------------------ #
    # Solver + replay
    # ------------------------------------------------------------------ #

    def solve_and_play(self, algo_name: str = "astar") -> None:
        if self.is_auto_playing:
            return

        solver_type = _SOLVER_TYPES.get(algo_name, SolverType.A_STAR)
        self.hud.update_stats(f"[{algo_name.upper()}] Calculating solution...")
        map_path = self._get_map_path(self.current_level_num)

        def worker() -> None:
            metrics = self._run_solver(solver_type, map_path)
            invoke(lambda: self._on_solver_finished(algo_name, metrics))

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _run_solver(
        solver_type: SolverType, map_path: str
    ):  # -> SolutionWithMetrics | None
        kwargs: dict = {}
        if solver_type == SolverType.A_STAR:
            kwargs = {
                "cost_calculator_type": CostCalculatorType.UNIFORM,
                "heuristic_calculator_type": HeuristicCalculatorType.TELEPORT_AWARE,
            }
        try:
            return SolverRunner(solver_type, map_path, **kwargs).solve_for_metrics()
        except Exception as exc:  # noqa: BLE001 - surface any solver failure
            print(f"\n[ERROR] Solver execution failed: {exc}")
            traceback.print_exc()
            return None

    def _on_solver_finished(self, algo_name: str, metrics) -> None:
        if not metrics or not metrics.solution:
            self.hud.update_stats(f"[{algo_name.upper()}] No solution found!")
            return

        actions, _cost = metrics.solution

        def start_replay() -> None:
            self.hud.update_stats(
                f"[{algo_name.upper()} - LEVEL {self.current_level_num:02d}]\n"
                f"Steps: {metrics.solution_length} | Time: {metrics.search_time_in_secs:.4f}s\n"
                f"Expanded: {metrics.expanded_notes} | Peak Mem: {metrics.peak_memory_in_mb:.2f} MB"
            )
            self.is_auto_playing = True
            self._replay_step(actions, 0, self._replay_id)

        self.restart_with_fly_up(on_complete=start_replay, update_hud=False)

    def _replay_step(self, actions: list[Action], index: int, replay_id: int) -> None:
        if not self.is_auto_playing or replay_id != self._replay_id:
            return
        if index >= len(actions):
            self.is_auto_playing = False
            return

        def schedule_next() -> None:
            if self.is_auto_playing and replay_id == self._replay_id:
                invoke(
                    lambda: self._replay_step(actions, index + 1, replay_id),
                    delay=_AUTOPLAY_STEP_DELAY,
                )

        self.handle_action(actions[index], on_complete=schedule_next)

    # ------------------------------------------------------------------ #
    # Action handling
    # ------------------------------------------------------------------ #

    def _find_successor(self, action: Action) -> State | None:
        """Return the engine's next state for ``action``, or None if illegal."""
        for move_action, next_state in self.game.successors(self.state):
            if move_action == action:
                return next_state
        return None

    def handle_action(
        self, action: Action, on_complete: Callback | None = None
    ) -> None:
        if self.block.is_animating or self.game.is_goal(self.state):
            return

        next_state = self._find_successor(action)

        if self.state.is_split():
            self._handle_split_action(action, next_state, on_complete)
        else:
            self._handle_whole_action(action, next_state, on_complete)

    # ---- whole block ------------------------------------------------- #

    def _handle_whole_action(
        self, action: Action, next_state: State | None, on_complete: Callback | None
    ) -> None:
        if action is Action.SWITCH_CONTROL:
            if on_complete:
                on_complete()
            return

        pose = BlockPose.from_state(self.state)
        target = pose.after(action)
        pivot, axis = pose.roll_pivot(action)

        if next_state is None:
            on_roll_done: Callback = lambda: self._fail_whole_block(target)  # noqa: E731
        else:
            self._count_manual_move()
            on_roll_done = lambda: self._arrive_whole_block(next_state, on_complete)  # noqa: E731

        self.block.animate_roll(
            pivot,
            axis,
            target.row,
            target.col,
            target.orientation.value,
            on_complete=on_roll_done,
        )

    def _arrive_whole_block(
        self, next_state: State, on_complete: Callback | None
    ) -> None:
        self._commit_state(next_state)

        if next_state.is_split():
            first = next_state.get_first_coords()
            second = next_state.get_second_coords()
            self._cube_slots = {1: first, 2: second}
            self.block.split_into_cubes(first, second)
            # The Block starts with slot 1 active; follow the engine's choice.
            if next_state.get_controlled_cube_coords() == second:
                self.block.switch_active_cube()
            if on_complete:
                on_complete()
            return

        self._finish_or_continue(on_complete)

    def _fail_whole_block(self, target: BlockPose) -> None:
        def fall() -> None:
            self.block.animate_fall(
                level=self.level,
                r=target.row,
                c=target.col,
                ori=target.orientation.value,
                bridges_mask=self.state.get_bridges_open_states(),
                on_finish=lambda: self.reset_game(drop_in=True),
            )

        breaks_tile = target.orientation is Orientation.STANDING and (
            self.level.is_fragile_tile((target.row, target.col))
        )
        if breaks_tile:
            self.board.animate_break_tile(target.row, target.col)
            invoke(fall, delay=0.15)
        else:
            fall()

    # ---- split cubes ------------------------------------------------- #

    def _handle_split_action(
        self, action: Action, next_state: State | None, on_complete: Callback | None
    ) -> None:
        if action is Action.SWITCH_CONTROL:
            if next_state is not None:
                self.state = next_state
                self.block.switch_active_cube()
            if on_complete:
                on_complete()
            return

        controlled = self.state.get_controlled_cube_coords()
        if controlled is None:
            raise RuntimeError("Split state without a controlled cube")

        slot = self._slot_at(controlled)
        d_row, d_col = _DIRECTION_DELTAS[action]
        destination = (controlled[0] + d_row, controlled[1] + d_col)

        if next_state is None:
            on_roll_done: Callback = lambda: self.block.animate_cube_fall(  # noqa: E731
                slot, on_finish=lambda: self.reset_game(drop_in=True)
            )
        else:
            self._count_manual_move()
            on_roll_done = lambda: self._arrive_cube(  # noqa: E731
                next_state, slot, destination, on_complete
            )

        self.block.animate_cube_roll(
            slot, action.value, destination[0], destination[1], on_complete=on_roll_done
        )

    def _arrive_cube(
        self,
        next_state: State,
        slot: int,
        destination: Coordinate,
        on_complete: Callback | None,
    ) -> None:
        self._commit_state(next_state)

        if next_state.is_split():
            self._cube_slots[slot] = destination
            if on_complete:
                on_complete()
            return

        # The two cubes touched: merge them back into one block.
        self._cube_slots.clear()
        pose = BlockPose.from_state(next_state)
        self.block.merge_cubes(
            pose.row,
            pose.col,
            pose.orientation.value,
            on_complete=lambda: self._finish_or_continue(on_complete),
        )

    def _slot_at(self, coords: Coordinate) -> int:
        """Which cube sprite is standing on ``coords``."""
        for slot, position in self._cube_slots.items():
            if position == coords:
                return slot
        raise RuntimeError(
            f"No cube sprite tracked at {coords}; slots={self._cube_slots}"
        )

    # ---- shared ------------------------------------------------------ #

    def _commit_state(self, new_state: State) -> None:
        self.state = new_state
        self.board.sync_bridges(new_state.get_bridges_open_states())

    def _finish_or_continue(self, on_complete: Callback | None) -> None:
        if self.game.is_goal(self.state):
            self.block.animate_win(on_finish=self._on_win_finished)
        elif on_complete:
            on_complete()

    def _on_win_finished(self) -> None:
        self.is_auto_playing = False
        self.hud.update_stats(self.hud.stats_text.text + "\nSTAGE CLEAR!")
