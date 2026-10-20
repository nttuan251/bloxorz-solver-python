from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ursina import invoke

from src.game.core.action import Action
from src.game.core.coordinate import Coordinate
from src.gui.controller.stage import Stage
from src.gui.geometry import DIRECTION_DELTAS, BlockPose, Orientation

if TYPE_CHECKING:
    from src.game.core.state import State

Callback = Callable[[], None]


class ActionExecutor:
    def __init__(
        self,
        stage: Stage,
        on_move: Callback,
        on_failure: Callback,
        on_win: Callback,
    ) -> None:
        self.stage = stage
        self._on_move = on_move
        self._on_failure = on_failure
        self._on_win = on_win
        self._cube_slots: dict[int, Coordinate] = {}

    def reset(self) -> None:
        self._cube_slots.clear()

    def handle_action(
        self, action: Action, on_complete: Callback | None = None
    ) -> None:
        stage = self.stage
        if stage.block.is_animating or stage.is_goal():
            return

        next_state = stage.find_successor(action)
        if stage.state.is_split():
            self._handle_split(action, next_state, on_complete)
        else:
            self._handle_whole(action, next_state, on_complete)

    def _handle_whole(
        self, action: Action, next_state: State | None, on_complete: Callback | None
    ) -> None:
        if action is Action.SWITCH_CONTROL:
            if on_complete:
                on_complete()
            return

        pose = BlockPose.from_state(self.stage.state)
        target = pose.after(action)
        pivot, axis = pose.roll_pivot(action)

        if next_state is None:
            on_roll_done: Callback = lambda: self._fail_whole(target)  # noqa: E731
        else:
            self._on_move()
            on_roll_done = lambda: self._arrive_whole(next_state, on_complete)  # noqa: E731

        self.stage.block.animate_roll(
            pivot,
            axis,
            target.row,
            target.col,
            target.orientation.value,
            on_complete=on_roll_done,
        )

    def _arrive_whole(self, next_state: State, on_complete: Callback | None) -> None:
        self.stage.commit_state(next_state)

        if next_state.is_split():
            first = next_state.get_first_coords()
            second = next_state.get_second_coords()
            self._cube_slots = {1: first, 2: second}
            self.stage.block.split_into_cubes(first, second)
            # The Block starts with slot 1 active; follow the engine's choice.
            if next_state.get_controlled_cube_coords() == second:
                self.stage.block.switch_active_cube()
            if on_complete:
                on_complete()
            return

        self._finish_or_continue(on_complete)

    def _fail_whole(self, target: BlockPose) -> None:
        stage = self.stage

        def fall() -> None:
            stage.block.animate_fall(
                level=stage.level,
                r=target.row,
                c=target.col,
                ori=target.orientation.value,
                bridges_mask=stage.state.get_bridges_open_states(),
                on_finish=self._on_failure,
            )

        breaks_tile = (
            target.orientation is Orientation.STANDING
            and stage.level.is_fragile_tile((target.row, target.col))
        )
        if breaks_tile:
            stage.board.animate_break_tile(target.row, target.col)
            invoke(fall, delay=0.15)
        else:
            fall()

    def _handle_split(
        self, action: Action, next_state: State | None, on_complete: Callback | None
    ) -> None:
        stage = self.stage

        if action is Action.SWITCH_CONTROL:
            if next_state is not None:
                stage.state = next_state
                stage.block.switch_active_cube()
            if on_complete:
                on_complete()
            return

        controlled = stage.state.get_controlled_cube_coords()
        if controlled is None:
            raise RuntimeError("Split state without a controlled cube")

        slot = self._slot_at(controlled)
        d_row, d_col = DIRECTION_DELTAS[action]
        destination = (controlled[0] + d_row, controlled[1] + d_col)

        if next_state is None:
            on_roll_done: Callback = lambda: stage.block.animate_cube_fall(  # noqa: E731
                slot, on_finish=self._on_failure
            )
        else:
            self._on_move()
            on_roll_done = lambda: self._arrive_cube(  # noqa: E731
                next_state, slot, destination, on_complete
            )

        stage.block.animate_cube_roll(
            slot, action.value, destination[0], destination[1], on_complete=on_roll_done
        )

    def _arrive_cube(
        self,
        next_state: State,
        slot: int,
        destination: Coordinate,
        on_complete: Callback | None,
    ) -> None:
        self.stage.commit_state(next_state)

        if next_state.is_split():
            self._cube_slots[slot] = destination
            if on_complete:
                on_complete()
            return

        self._cube_slots.clear()
        pose = BlockPose.from_state(next_state)
        self.stage.block.merge_cubes(
            pose.row,
            pose.col,
            pose.orientation.value,
            on_complete=lambda: self._finish_or_continue(on_complete),
        )

    def _slot_at(self, coords: Coordinate) -> int:
        for slot, position in self._cube_slots.items():
            if position == coords:
                return slot
        raise RuntimeError(
            f"No cube sprite tracked at {coords}; slots={self._cube_slots}"
        )

    def _finish_or_continue(self, on_complete: Callback | None) -> None:
        if self.stage.is_goal():
            self.stage.block.animate_win(on_finish=self._on_win)
        elif on_complete:
            on_complete()
