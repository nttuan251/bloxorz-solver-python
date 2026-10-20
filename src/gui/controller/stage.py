from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ursina import Vec3

from src.game.core.action import Action
from src.game.logic.engine import BloxorzGame
from src.game.logic.level_loader import LevelLoader
from src.gui.geometry import Orientation
from src.gui.view.block.block import Block
from src.gui.view.board import Board

if TYPE_CHECKING:
    from src.game.core.level import Level
    from src.game.core.state import State

Callback = Callable[[], None]


class Stage:
    def __init__(self, level_num: int, map_path: str) -> None:
        self.level_num = level_num
        self.level: Level = LevelLoader.parse_level_from_file(map_path)
        self.game = BloxorzGame(self.level)
        self.state: State = self.game.start_state()

        start_row, start_col = self.level.get_start()
        self.board = Board(self.level, animate_entrance=True, start_delay=0.3)
        self.board.sync_bridges(
            self.state.get_bridges_open_states(), animate_entrance=True
        )
        self.block = Block(start_row, start_col)
        self.block.animate_drop_in(
            start_row, start_col, delay=self.board.get_entrance_duration()
        )

    @property
    def spawn_position(self) -> Vec3:
        row, col = self.level.get_start()
        return Vec3(col, 0, -row)

    def is_goal(self) -> bool:
        return self.game.is_goal(self.state)

    def block_is_visible(self) -> bool:
        entity = self.block.entity
        return bool(entity and entity.enabled and not self.is_goal())

    def find_successor(self, action: Action) -> State | None:
        """Return the engine's next state for ``action``, or None if illegal."""
        for move_action, next_state in self.game.successors(self.state):
            if move_action == action:
                return next_state
        return None

    def commit_state(self, new_state: State) -> None:
        self.state = new_state
        self.board.sync_bridges(new_state.get_bridges_open_states())

    def reset(self, drop_in: bool = False, on_complete: Callback | None = None) -> None:
        self.state = self.game.start_state()
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

    def reset_bridges_to_start(self) -> None:
        self.board.sync_bridges(self.game.start_state().get_bridges_open_states())

    def animate_exit(self, on_complete: Callback) -> None:
        self.block.animate_exit_fly_up(duration=0.4)
        self.board.animate_exit_fall_down(pause_duration=0.35, on_complete=on_complete)

    def destroy(self) -> None:
        self.board.destroy_board()
        self.block.destroy_block()
