"""3D block renderer driven by core State (single block or 2 split cubes)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ursina import Entity, Vec3, color, curve, destroy, invoke, scene

import config as config
from core.state import State
from core.tile import Action


def _pivot_for(r: int, c: int, ori: str, action: Action):
    """Pivot position + rotation axis reused from the classic roll table."""
    if ori == 'STANDING':
        mapping = {
            'RIGHT': ((c + 0.5, 0, -r), (0, 0, 90)),
            'LEFT': ((c - 0.5, 0, -r), (0, 0, -90)),
            'UP': ((c, 0, -r + 0.5), (90, 0, 0)),
            'DOWN': ((c, 0, -r - 0.5), (-90, 0, 0)),
        }
    elif ori == 'LYING_H':
        mapping = {
            'RIGHT': ((c + 1.5, 0, -r), (0, 0, 90)),
            'LEFT': ((c - 0.5, 0, -r), (0, 0, -90)),
            'UP': ((c + 0.5, 0, -r + 0.5), (90, 0, 0)),
            'DOWN': ((c + 0.5, 0, -r - 0.5), (-90, 0, 0)),
        }
    else:  # LYING_V
        mapping = {
            'RIGHT': ((c + 0.5, 0, -(r + 0.5)), (0, 0, 90)),
            'LEFT': ((c - 0.5, 0, -(r + 0.5)), (0, 0, -90)),
            'UP': ((c, 0, -r + 0.5), (90, 0, 0)),
            'DOWN': ((c, 0, -(r + 1.5)), (-90, 0, 0)),
        }
    # LYING_V DOWN entry above is ((pivot),(axis)); fix tuple shape.
    val = mapping[action.value]
    if len(val) == 2 and isinstance(val[0], tuple):
        return val
    return val[0], val[1]


class Block:
    def __init__(self):
        self.main = Entity(model='cube', color=config.BLOCK_COLOR)
        self.cube_a = Entity(model='cube', color=config.CUBE_ACTIVE,
                             scale=(0.9, 0.9, 0.9))
        self.cube_b = Entity(model='cube', color=config.CUBE_IDLE,
                             scale=(0.9, 0.9, 0.9))
        self.is_animating = False
        self._split = False

    # ---------- immediate sync (no animation) ----------
    @staticmethod
    def _stand_pos(r, c):
        return Vec3(c, 1.0, -r), Vec3(0.9, 2.0, 0.9)

    @staticmethod
    def _lying_h_pos(r, c):
        return Vec3(c + 0.5, 0.5, -r), Vec3(1.9, 0.9, 0.9)

    @staticmethod
    def _lying_v_pos(r, c):
        return Vec3(c, 0.5, -(r + 0.5)), Vec3(0.9, 0.9, 1.9)

    @staticmethod
    def _cube_pos(r, c):
        return Vec3(c, 0.55, -r)

    def sync(self, state: State):
        """Snap visuals to `state` instantly."""
        self._split = state.split
        self.main.enabled = not state.split
        self.cube_a.enabled = state.split
        self.cube_b.enabled = state.split
        if not state.split:
            if state.is_standing():
                pos, scl = self._stand_pos(*state.a)
            elif state.a[0] == state.b[0]:
                pos, scl = self._lying_h_pos(*state.a)
            else:
                pos, scl = self._lying_v_pos(*state.a)
            self.main.position = pos
            self.main.scale = scl
            self.main.rotation = Vec3(0, 0, 0)
        else:
            self.cube_a.position = self._cube_pos(*state.a)
            self.cube_b.position = self._cube_pos(*state.b)
            self.cube_a.color = (config.CUBE_ACTIVE if state.active == 0
                                 else config.CUBE_IDLE)
            self.cube_b.color = (config.CUBE_ACTIVE if state.active == 1
                                 else config.CUBE_IDLE)

    # ---------- animated transition ----------
    def animate_to(self, old: State, action: Action, new: State, done=None):
        """Animate old -action-> new, then sync + call done()."""
        def _finish():
            self.sync(new)
            self.is_animating = False
            if done:
                done()

        if action == Action.SWITCH:
            self.is_animating = True
            self.sync(new)
            self.is_animating = False
            if done:
                invoke(done, delay=0.05)
            return

        # Teleport cases (split / merge): instant snap with a tiny pop.
        if old.split != new.split or (old.split and new.split and
                                      self._teleported(old, new)):
            self.is_animating = True
            invoke(_finish, delay=0.08)
            return

        if not old.split and not new.split:
            self._animate_roll(old, action, new, _finish)
            return

        # Cube slide (one cube moves one cell).
        if old.split and new.split:
            self._animate_cube_slide(old, new, _finish)
            return

        self.is_animating = True
        invoke(_finish, delay=0.08)

    @staticmethod
    def _teleported(old: State, new: State) -> bool:
        moved_a = abs(old.a[0] - new.a[0]) + abs(old.a[1] - new.a[1])
        moved_b = abs(old.b[0] - new.b[0]) + abs(old.b[1] - new.b[1])
        return moved_a + moved_b > 2

    def _animate_roll(self, old: State, action: Action, new: State, _finish):
        self.is_animating = True
        r, c = old.a
        ori = old.orientation()
        try:
            pivot_pos, rot_axis = _pivot_for(r, c, ori, action)
        except KeyError:
            self.sync(new)
            self.is_animating = False
            _finish()
            return
        pivot = Entity(position=Vec3(*pivot_pos))
        self.main.world_parent = pivot
        try:
            pivot.animate_rotation(Vec3(*rot_axis),
                                   duration=config.ROLL_DURATION,
                                   curve=curve.linear)
        except Exception:
            pass

        def finish():
            try:
                self.main.world_parent = scene
            except Exception:
                pass
            destroy(pivot)
            _finish()

        invoke(finish, delay=config.ROLL_DURATION + 0.02)

    def _animate_cube_slide(self, old: State, new: State, _finish):
        self.is_animating = True
        mover = self.cube_a if old.active == 0 else self.cube_b
        target = (new.a if old.active == 0 else new.b)
        try:
            mover.animate_position(self._cube_pos(*target),
                                   duration=config.CUBE_DURATION,
                                   curve=curve.linear)
        except Exception:
            pass
        invoke(_finish, delay=config.CUBE_DURATION + 0.02)

    # ---------- fall ----------
    def animate_fall(self, done=None):
        """Legacy in-place drop (fallback). Prefer animate_roll_then_fall."""
        self.is_animating = True

        def _end():
            self.is_animating = False
            if done:
                done()

        try:
            # Drop whichever is visible: drop all for simplicity.
            for e in (self.main, self.cube_a, self.cube_b):
                if e.enabled:
                    e.animate_position(e.position + Vec3(0, -4, 0),
                                       duration=0.5, curve=curve.linear)
        except Exception:
            pass
        invoke(_end, delay=0.55)

    def animate_roll_then_fall(self, old: State, action: Action,
                               preview: tuple | None, done=None):
        """Roll out to `preview` cells (may be off-board) then drop down."""
        self.is_animating = True

        def _drop(entity, delay_after=0.0):
            try:
                entity.animate_position(entity.position + Vec3(0, -4, 0),
                                        duration=config.FALL_DURATION,
                                        curve=curve.linear)
            except Exception:
                pass
            invoke(_end, delay=config.FALL_DURATION + 0.05 + delay_after)

        def _end():
            self.is_animating = False
            if done:
                done()

        if preview is None:
            self.animate_fall(done=done)
            self.is_animating = True  # animate_fall resets itself; keep flag
            return

        # --- split cube falls: slide the active cube out, then drop it ---
        if old.split:
            mover = self.cube_a if old.active == 0 else self.cube_b
            try:
                mover.animate_position(self._cube_pos(*preview[0]),
                                       duration=config.CUBE_DURATION,
                                       curve=curve.linear)
            except Exception:
                pass

            def _drop_mover():
                _drop(mover)

            invoke(_drop_mover, delay=config.CUBE_DURATION + 0.02)
            return

        # --- block rolls out, then the whole block drops ---
        try:
            preview_pos, preview_scl = self._transform_for_cells(preview)
        except Exception:
            self.animate_fall(done=done)
            return
        r, c = old.a
        try:
            pivot_pos, rot_axis = _pivot_for(r, c, old.orientation(), action)
        except KeyError:
            # Unknown geometry: snap out then drop.
            self.main.position, self.main.scale = preview_pos, preview_scl
            _drop(self.main)
            return
        pivot = Entity(position=Vec3(*pivot_pos))
        self.main.world_parent = pivot
        try:
            pivot.animate_rotation(Vec3(*rot_axis),
                                   duration=config.ROLL_DURATION,
                                   curve=curve.linear)
        except Exception:
            pass

        def _after_roll():
            try:
                self.main.world_parent = scene
            except Exception:
                pass
            self.main.position, self.main.scale = preview_pos, preview_scl
            try:
                self.main.rotation = Vec3(0, 0, 0)
            except Exception:
                pass
            _drop(self.main)
            try:
                destroy(pivot)
            except Exception:
                pass

        invoke(_after_roll, delay=config.ROLL_DURATION + 0.02)

    @staticmethod
    def _transform_for_cells(cells: tuple):
        uniq = tuple(sorted(set(cells)))
        if len(uniq) == 1:
            return Block._stand_pos(*uniq[0])
        (r1, c1), (r2, c2) = uniq[0], uniq[1]
        if r1 == r2:
            return Block._lying_h_pos(min(r1, r2), min(c1, c2))
        if c1 == c2:
            return Block._lying_v_pos(min(r1, r2), min(c1, c2))
        # Non-adjacent (should not happen for falls): stand on first cell.
        return Block._stand_pos(*uniq[0])

    def destroy(self):
        for e in (self.main, self.cube_a, self.cube_b):
            try:
                destroy(e)
            except Exception:
                pass
