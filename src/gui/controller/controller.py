from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ursina import Vec3

from src.game.core.action import Action
from src.gui.controller.action_executor import ActionExecutor
from src.gui.controller.camera_rig import CameraRig
from src.gui.controller.solver_playback import SolverPlayback, SolverRequest
from src.gui.controller.stage import Stage
from src.gui.ui import HUD

Callback = Callable[[], None]

_KEY_BINDINGS: dict[str, Action] = {
    "right arrow": Action.RIGHT,
    "left arrow": Action.LEFT,
    "up arrow": Action.UP,
    "down arrow": Action.DOWN,
    "space": Action.SWITCH_CONTROL,
}


class GameController:
    def __init__(self, max_levels: int = 33) -> None:
        self.max_levels = max_levels
        self.current_level_num = 1
        self.manual_moves = 0

        self._stage: Stage | None = None
        self._executor: ActionExecutor | None = None

        self.camera_rig = CameraRig()
        self.hud = HUD(
            on_solve_click=self.solve_and_play,
            on_manual_click=self.switch_to_manual,
            on_level_change=self.change_level,
            on_select_level=self.select_stage_direct,
            on_restart_click=lambda: self.restart_with_fly_up(update_hud=True),
            max_levels=self.max_levels,
        )
        self.playback = SolverPlayback(
            hud=self.hud,
            execute_action=lambda action, done: self.handle_action(
                action, on_complete=done
            ),
            restart=lambda done: self.restart_with_fly_up(
                on_complete=done, update_hud=False
            ),
        )

        self.load_stage(self.current_level_num)

    @property
    def stage(self) -> Stage:
        if self._stage is None:
            raise RuntimeError("No stage loaded")
        return self._stage

    @property
    def executor(self) -> ActionExecutor:
        if self._executor is None:
            raise RuntimeError("No stage loaded")
        return self._executor

    @property
    def is_auto_playing(self) -> bool:
        return self.playback.is_playing

    def update(self) -> None:
        if self._stage is None:
            return
        cube = self._stage.block.get_active_cube()
        follow = Vec3(cube.world_x, 0, cube.world_z) if cube else None
        self.camera_rig.update(follow)

    def handle_input(self, key: str) -> None:
        if self.camera_rig.handle_scroll(key) or self.is_auto_playing:
            return

        if key in _KEY_BINDINGS:
            self.handle_action(_KEY_BINDINGS[key])
        elif key == "r":
            self.restart_with_fly_up(update_hud=True)

    def handle_action(
        self, action: Action, on_complete: Callback | None = None
    ) -> None:
        self.executor.handle_action(action, on_complete)

    @staticmethod
    def _get_map_path(level_num: int) -> str:
        json_path = f"maps/level_{level_num:02d}.json"
        if Path(json_path).exists():
            return json_path
        return f"maps/level_{level_num:02d}.txt"

    def load_stage(self, level_num: int) -> None:
        self.current_level_num = level_num
        self.playback.cancel()
        self.manual_moves = 0

        if self._stage is None:
            self._build_stage(level_num)
        else:
            self._stage.animate_exit(on_complete=lambda: self._build_stage(level_num))

    def _build_stage(self, level_num: int) -> None:
        if self._stage is not None:
            self._stage.destroy()

        self._stage = Stage(level_num, self._get_map_path(level_num))
        self._executor = ActionExecutor(
            self._stage,
            on_move=self._count_manual_move,
            on_failure=lambda: self.reset_game(drop_in=True),
            on_win=self._on_win_finished,
        )
        self.camera_rig.snap_to(self._stage.spawn_position)
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
        self.playback.cancel()
        self.manual_moves = 0
        if update_hud:
            self._show_manual_stats()

        self.executor.reset()
        self.stage.reset(drop_in=drop_in, on_complete=on_complete)

    def restart_with_fly_up(
        self, on_complete: Callback | None = None, update_hud: bool = True
    ) -> None:
        self.playback.cancel()
        self.stage.reset_bridges_to_start()

        def reset_with_drop_in() -> None:
            self.reset_game(
                drop_in=True, on_complete=on_complete, update_hud=update_hud
            )

        if self.stage.block_is_visible():
            self.stage.block.animate_exit_fly_up(
                duration=0.35, on_complete=reset_with_drop_in
            )
        else:
            reset_with_drop_in()

    def solve_and_play(self, algo_name: str = "astar") -> None:
        self.playback.solve_and_play(
            SolverRequest(
                algo_name=algo_name,
                map_path=self._get_map_path(self.current_level_num),
                level_num=self.current_level_num,
                cost_type=self.hud.selected_cost,
                heuristic_type=self.hud.selected_heuristic,
            )
        )

    def _show_manual_stats(self) -> None:
        self.hud.update_stats(
            f"[LEVEL {self.current_level_num:02d} - MANUAL MODE]\nMoves: {self.manual_moves}"
        )

    def _count_manual_move(self) -> None:
        if not self.is_auto_playing:
            self.manual_moves += 1
            self._show_manual_stats()

    def _on_win_finished(self) -> None:
        self.playback.is_playing = False
        self.hud.update_stats(self.hud.stats_text.text + "\nSTAGE CLEAR!")
