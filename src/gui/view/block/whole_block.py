from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Entity, Vec3, curve

from src.gui import config
from src.gui.geometry import Orientation
from src.gui.view.block.animation import (
    AnimationGate,
    Callback,
    attach_pivot,
    release_pivot,
    sink_into_void,
    stop_animations,
)
from src.gui.view.block.block_style import WHOLE_COLOR, transform_for

if TYPE_CHECKING:
    from src.game.core.level import Level


_DROP_IN_HEIGHT = 12.0
_DROP_IN_DURATION = 0.55
_TIP_DURATION = 0.2
_TIP_FALL_DURATION = 0.5
_WIN_DURATION = 0.45
_FLY_UP_DISTANCE = 15


class WholeBlock:
    def __init__(self, gate: AnimationGate, start_r: int, start_c: int) -> None:
        self._gate = gate
        self.entity = Entity(model="cube", color=WHOLE_COLOR, texture="white_cube")
        self.set_transform(start_r, start_c, Orientation.STANDING)

    # ---- state ------------------------------------------------------- #

    def set_transform(self, r: int, c: int, ori: Orientation | str) -> None:
        pos, scale = transform_for(r, c, ori)
        self.entity.position = pos
        self.entity.scale = scale
        self.entity.rotation = Vec3(0, 0, 0)
        self.entity.color = WHOLE_COLOR

    def show(self) -> None:
        self.entity.enabled = True
        self.entity.color = WHOLE_COLOR

    def hide(self) -> None:
        self.entity.enabled = False

    def roll(
        self,
        pivot_pos: tuple[float, float, float],
        rot_axis: tuple[float, float, float],
        next_r: int,
        next_c: int,
        next_ori: Orientation | str,
        on_complete: Callback | None = None,
    ) -> None:
        self._gate.begin()
        stop_animations(self.entity)
        pivot = attach_pivot(
            self.entity, Vec3(*pivot_pos), Vec3(*rot_axis), config.ROLL_DURATION
        )

        def settle() -> None:
            release_pivot(self.entity, pivot)
            self.set_transform(next_r, next_c, next_ori)

        self._gate.finish_after(config.ROLL_DURATION, on_complete, cleanup=settle)

    def fall(
        self,
        level: Level | None = None,
        r: int = 0,
        c: int = 0,
        ori: Orientation | str = Orientation.STANDING,
        bridges_mask: dict[tuple[int, int], bool] | None = None,
        on_finish: Callback | None = None,
    ) -> None:
        self._gate.begin()
        tip = self._find_tip(level, r, c, Orientation(ori), bridges_mask)

        if tip is None:
            sink_into_void(self.entity, self._gate, on_finish)
            return

        pivot_pos, rotation = tip
        pivot = attach_pivot(
            self.entity, pivot_pos, rotation, _TIP_DURATION, curve.in_quad
        )

        def drop_down() -> None:
            pivot.animate_position(
                pivot.position + Vec3(0, -10, 0),
                duration=_TIP_FALL_DURATION,
                curve=curve.in_quad,
            )
            self._gate.finish_after(
                _TIP_FALL_DURATION + 0.05,
                on_finish,
                cleanup=lambda: release_pivot(self.entity, pivot),
            )

        self._gate.schedule(_TIP_DURATION, drop_down)

    @staticmethod
    def _find_tip(
        level: Level | None,
        r: int,
        c: int,
        ori: Orientation,
        bridges_mask: dict[tuple[int, int], bool] | None,
    ) -> tuple[Vec3, Vec3] | None:
        def solid(tr: int, tc: int) -> bool:
            if level is None or bridges_mask is None:
                return False
            return level.is_valid_tile((tr, tc), bridges_mask)

        if ori is Orientation.LYING_H:
            first, second = solid(r, c), solid(r, c + 1)
            pivot = Vec3(c + 0.5, 0, -r)
            if first and not second:
                return pivot, Vec3(0, 0, 90)
            if second and not first:
                return pivot, Vec3(0, 0, -90)
        elif ori is Orientation.LYING_V:
            first, second = solid(r, c), solid(r + 1, c)
            pivot = Vec3(c, 0, -(r + 0.5))
            if first and not second:
                return pivot, Vec3(-90, 0, 0)
            if second and not first:
                return pivot, Vec3(90, 0, 0)
        return None

    def win(self, on_finish: Callback | None = None) -> None:
        e = self.entity
        e.animate_position(
            Vec3(e.x, -0.2, e.z), duration=_WIN_DURATION, curve=curve.in_quad
        )
        e.animate_scale(
            Vec3(0.85, 0.0, 0.85), duration=_WIN_DURATION, curve=curve.in_quad
        )
        self._gate.finish_after(_WIN_DURATION + 0.02, on_finish, cleanup=self.hide)

    def fly_up(self, duration: float, on_complete: Callback | None = None) -> None:
        self.entity.animate_position(
            self.entity.position + Vec3(0, _FLY_UP_DISTANCE, 0),
            duration=duration,
            curve=curve.in_back,
        )
        self._gate.finish_after(duration, on_complete)

    def drop_in(
        self, r: int, c: int, delay: float = 0.0, on_complete: Callback | None = None
    ) -> None:
        self._gate.begin()
        target_pos, target_scale = transform_for(r, c, Orientation.STANDING)
        e = self.entity
        e.position = Vec3(target_pos.x, _DROP_IN_HEIGHT, target_pos.z)
        e.scale = target_scale
        e.rotation = Vec3(0, 0, 0)
        e.color = WHOLE_COLOR

        def start_drop() -> None:
            e.enabled = True
            e.animate_position(
                target_pos, duration=_DROP_IN_DURATION, curve=curve.out_bounce
            )

            def settle() -> None:
                stop_animations(e)
                e.position = target_pos
                e.rotation = Vec3(0, 0, 0)

            def notify() -> None:
                if on_complete:
                    self._gate.schedule(0.08, on_complete)

            self._gate.finish_after(_DROP_IN_DURATION, notify, cleanup=settle)

        if delay > 0:
            e.enabled = False
            self._gate.schedule(delay, start_drop)
        else:
            start_drop()
