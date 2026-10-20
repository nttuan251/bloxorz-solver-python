"""Facade over WholeBlock + SplitCubes. Public API is unchanged for the controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Entity, destroy

from src.gui.geometry import Coordinate, Orientation
from src.gui.view.block.animation import AnimationGate, Callback, destroy_entity
from src.gui.view.block.block_style import transform_for
from src.gui.view.block.split_cubes import SplitCubes
from src.gui.view.block.whole_block import WholeBlock

if TYPE_CHECKING:
    from src.game.core.action import Action
    from src.game.core.level import Level


class Block:
    """Quản lý hiển thị và chuyển động hoạt ảnh của khối gạch (nguyên thể và khi tách đôi)."""

    def __init__(self, start_r: int, start_c: int) -> None:
        self._gate = AnimationGate()
        self._whole = WholeBlock(self._gate, start_r, start_c)
        self._split = SplitCubes(self._gate)

    # ---- state ------------------------------------------------------- #

    @property
    def is_animating(self) -> bool:
        return self._gate.busy

    @is_animating.setter
    def is_animating(self, value: bool) -> None:
        self._gate.busy = value

    @property
    def entity(self) -> Entity:
        return self._whole.entity

    @property
    def is_split(self) -> bool:
        return self._split.is_split

    def get_active_cube(self) -> Entity | None:
        """Trả về entity 3D của khối gạch đang được kích hoạt điều khiển."""
        return self._split.active_cube() if self.is_split else self._whole.entity

    def set_transform(self, r: int, c: int, ori: Orientation | str) -> None:
        self._whole.set_transform(r, c, ori)

    # ---- split / merge ------------------------------------------------ #

    def split_into_cubes(self, pos1: Coordinate, pos2: Coordinate) -> None:
        self.cleanup_split()
        self._whole.hide()
        self._split.split(pos1, pos2)

    def switch_active_cube(self) -> None:
        self._split.switch_active()

    def cleanup_split(self) -> None:
        """Hủy hai khối lập phương nhỏ và khôi phục hiển thị cho khối gạch nguyên thể."""
        self._split.clear()
        self._whole.show()

    def merge_cubes(
        self,
        target_r: int,
        target_c: int,
        target_ori: Orientation | str,
        on_complete: Callback | None = None,
    ) -> None:
        target_pos, _ = transform_for(target_r, target_c, target_ori)

        def finish() -> None:
            self.cleanup_split()
            self._whole.set_transform(target_r, target_c, target_ori)

        self._split.merge_to(target_pos, before_done=finish, on_complete=on_complete)

    # ---- split-cube animations --------------------------------------- #

    def animate_cube_roll(
        self,
        cube_index: int,
        action: Action | str,
        next_r: int,
        next_c: int,
        on_complete: Callback | None = None,
    ) -> None:
        self._split.roll(cube_index, action, next_r, next_c, on_complete)

    def animate_cube_fall(
        self, cube_index: int, on_finish: Callback | None = None
    ) -> None:
        self._split.fall(cube_index, on_finish)

    # ---- whole-block animations -------------------------------------- #

    def animate_roll(
        self,
        pivot_pos: tuple[float, float, float],
        rot_axis: tuple[float, float, float],
        next_r: int,
        next_c: int,
        next_ori: Orientation | str,
        on_complete: Callback | None = None,
    ) -> None:
        self._whole.roll(pivot_pos, rot_axis, next_r, next_c, next_ori, on_complete)

    def animate_fall(
        self,
        level: Level | None = None,
        r: int = 0,
        c: int = 0,
        ori: Orientation | str = Orientation.STANDING,
        bridges_mask: dict[Coordinate, bool] | None = None,
        on_finish: Callback | None = None,
    ) -> None:
        self._whole.fall(level, r, c, ori, bridges_mask, on_finish)

    def animate_win(self, on_finish: Callback | None = None) -> None:
        self._whole.win(on_finish)

    def animate_drop_in(
        self,
        target_r: int,
        target_c: int,
        delay: float = 0.0,
        on_complete: Callback | None = None,
    ) -> None:
        self._whole.drop_in(target_r, target_c, delay, on_complete)

    def animate_exit_fly_up(
        self, duration: float = 0.35, on_complete: Callback | None = None
    ) -> None:
        part = self._split if self.is_split else self._whole
        part.fly_up(duration, on_complete)

    def destroy_block(self) -> None:
        self._gate.close()
        self._split.clear()
        destroy_entity(self._whole.entity)
