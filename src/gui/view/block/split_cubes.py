from __future__ import annotations

from ursina import Entity, Vec3, curve
from ursina.shaders import lit_with_shadows_shader

from src.game.core.action import Action
from src.gui import config
from src.gui.geometry import BlockPose, Coordinate, Orientation
from src.gui.view.block.animation import (
    AnimationGate,
    Callback,
    attach_pivot,
    destroy_entity,
    release_pivot,
    sink_into_void,
    stop_animations,
)
from src.gui.view.block.block_style import (
    ACTIVE_CUBE_COLOR,
    CUBE_SCALE,
    INACTIVE_CUBE_COLOR,
    cube_position,
)

_MERGE_DURATION = 0.25
_FLY_UP_DISTANCE = 15


class SplitCubes:
    def __init__(self, gate: AnimationGate) -> None:
        self._gate = gate
        self._cubes: dict[int, Entity] = {}
        self._active_slot = 1

    @property
    def is_split(self) -> bool:
        return bool(self._cubes)

    def split(self, pos1: Coordinate, pos2: Coordinate) -> None:
        self.clear()
        for slot, (r, c) in ((1, pos1), (2, pos2)):
            self._cubes[slot] = Entity(
                model="cube",
                texture="white_cube",
                position=cube_position(r, c),
                scale=CUBE_SCALE,
                shader=lit_with_shadows_shader,
            )
        self._active_slot = 1
        self._update_styles()

    def clear(self) -> None:
        for cube in self._cubes.values():
            destroy_entity(cube)
        self._cubes.clear()

    def active_cube(self) -> Entity | None:
        return self._cubes.get(self._active_slot)

    def switch_active(self) -> None:
        if not self.is_split or self._gate.busy:
            return
        self._active_slot = 2 if self._active_slot == 1 else 1
        self._update_styles()

    def _update_styles(self) -> None:
        for slot, cube in self._cubes.items():
            cube.color = (
                ACTIVE_CUBE_COLOR if slot == self._active_slot else INACTIVE_CUBE_COLOR
            )

    def roll(
        self,
        slot: int,
        action: Action | str,
        next_r: int,
        next_c: int,
        on_complete: Callback | None = None,
    ) -> None:
        self._gate.begin()
        cube = self._cubes[slot]
        stop_animations(cube)

        r = round(-cube.z)
        c = round(cube.x)
        # A lone cube pivots exactly like a standing block of one tile.
        pivot_pos, rot_axis = BlockPose(r, c, Orientation.STANDING).roll_pivot(
            Action(action)
        )
        pivot = attach_pivot(
            cube, Vec3(*pivot_pos), Vec3(*rot_axis), config.ROLL_DURATION
        )

        def settle() -> None:
            release_pivot(cube, pivot)
            cube.position = cube_position(next_r, next_c)
            cube.rotation = Vec3(0, 0, 0)

        self._gate.finish_after(config.ROLL_DURATION, on_complete, cleanup=settle)

    def fall(self, slot: int, on_finish: Callback | None = None) -> None:
        self._gate.begin()
        sink_into_void(self._cubes[slot], self._gate, on_finish)

    def merge_to(
        self,
        target: Vec3,
        before_done: Callback,
        on_complete: Callback | None = None,
    ) -> None:
        for cube in self._cubes.values():
            cube.animate_position(
                target, duration=_MERGE_DURATION, curve=curve.in_out_quad
            )
        self._gate.finish_after(
            _MERGE_DURATION + 0.03, on_complete, cleanup=before_done
        )

    def fly_up(self, duration: float, on_complete: Callback | None = None) -> None:
        for cube in self._cubes.values():
            cube.animate_position(
                cube.position + Vec3(0, _FLY_UP_DISTANCE, 0),
                duration=duration,
                curve=curve.in_back,
            )
        self._gate.finish_after(duration, on_complete)
