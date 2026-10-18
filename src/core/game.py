"""Single source of truth for Bloxorz rules (used by GUI + all solvers)."""

from __future__ import annotations

from .level import Level
from .state import State
from .tile import ACTION_ORDER, Action, BridgeMode, SwitchKind

Coord = tuple[int, int]
_DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


class BloxorzGame:
    """Transition model. Cost is uniform 1 per action (report baseline)."""

    def __init__(self, level: Level):
        self.level = level
        self._bridge_idx = {bid: i for i, bid in enumerate(level.bridge_order)}

    # ---------- public API ----------
    def start_state(self) -> State:
        r, c = self.level.start
        return State.standing(r, c, self.level.initial_mask())

    def is_goal(self, s: State) -> bool:
        return (not s.split) and s.is_standing() and s.a == self.level.goal

    def successors(self, s: State) -> list[tuple[Action, State, float]]:
        out: list[tuple[Action, State, float]] = []
        for a in ACTION_ORDER:
            nxt = self.apply(s, a)
            if nxt is not None:
                out.append((a, nxt, 1.0))
        return out

    def apply(self, s: State, a: Action) -> State | None:
        """Return next state or None if the move is illegal (fall)."""
        if a == Action.SWITCH:
            return self._apply_switch_cube(s)
        if s.split:
            return self._move_cube(s, a)
        return self._move_block(s, a)

    def preview_cells(self, s: State, a: Action) -> tuple[Coord, ...] | None:
        """Cells the block/cube *would* occupy, ignoring support/fragile.

        Used only for fall animation (roll out then drop). Returns None when
        the action causes no displacement (e.g. SWITCH).
        """
        if a == Action.SWITCH:
            return None
        if s.split:
            if a not in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT):
                return None
            dr, dc = _DELTA[a.value]
            cur = s.active_pos()
            return ((cur[0] + dr, cur[1] + dc),)
        occ = s.occupied()
        if len(occ) == 1:
            (r, c) = occ[0]
            if a == Action.UP:
                return ((r - 2, c), (r - 1, c))
            if a == Action.DOWN:
                return ((r + 1, c), (r + 2, c))
            if a == Action.LEFT:
                return ((r, c - 2), (r, c - 1))
            if a == Action.RIGHT:
                return ((r, c + 1), (r, c + 2))
            return None
        (r1, c1), (r2, c2) = occ
        if r1 == r2:  # LYING_H
            r, c = r1, min(c1, c2)
            if a == Action.UP:
                return ((r - 1, c), (r - 1, c + 1))
            if a == Action.DOWN:
                return ((r + 1, c), (r + 1, c + 1))
            if a == Action.LEFT:
                return ((r, c - 1),)
            if a == Action.RIGHT:
                return ((r, c + 2),)
            return None
        r, c = min(r1, r2), c1  # LYING_V
        if a == Action.UP:
            return ((r - 1, c),)
        if a == Action.DOWN:
            return ((r + 2, c),)
        if a == Action.LEFT:
            return ((r, c - 1), (r + 1, c - 1))
        if a == Action.RIGHT:
            return ((r, c + 1), (r + 1, c + 1))
        return None

    # ---------- normal 1x1x2 block ----------
    def _move_block(self, s: State, a: Action) -> State | None:
        occ = s.occupied()
        if len(occ) == 1:
            (r, c) = occ[0]
            if a == Action.UP:
                na, nb = (r - 2, c), (r - 1, c)
            elif a == Action.DOWN:
                na, nb = (r + 1, c), (r + 2, c)
            elif a == Action.LEFT:
                na, nb = (r, c - 2), (r, c - 1)
            elif a == Action.RIGHT:
                na, nb = (r, c + 1), (r, c + 2)
            else:
                return None
        else:
            (r1, c1), (r2, c2) = occ
            if r1 == r2:  # LYING_H on (r,c)-(r,c+1)
                r, c = r1, min(c1, c2)
                if a == Action.UP:
                    na, nb = (r - 1, c), (r - 1, c + 1)
                elif a == Action.DOWN:
                    na, nb = (r + 1, c), (r + 1, c + 1)
                elif a == Action.LEFT:
                    na, nb = (r, c - 1), (r, c - 1)
                elif a == Action.RIGHT:
                    na, nb = (r, c + 2), (r, c + 2)
                else:
                    return None
            else:  # LYING_V
                r, c = min(r1, r2), c1
                if a == Action.UP:
                    na, nb = (r - 1, c), (r - 1, c)
                elif a == Action.DOWN:
                    na, nb = (r + 2, c), (r + 2, c)
                elif a == Action.LEFT:
                    na, nb = (r, c - 1), (r + 1, c - 1)
                elif a == Action.RIGHT:
                    na, nb = (r, c + 1), (r + 1, c + 1)
                else:
                    return None

        standing = (na == nb)
        # 1. support check with CURRENT bridge mask (closed bridge = void).
        for cell in ({na} if standing else {na, nb}):
            if not self._has_tile(cell, s.bridges):
                return None
        # 2. fragile: standing on fragile breaks.
        if standing and na in self.level.fragile:
            return None

        mask = list(s.bridges)
        # 3. switch effects (toggle each time we step onto it).
        if standing:
            sw = self.level.switch_at.get(na)
            if sw is not None:
                if sw.kind == SwitchKind.SPLIT:
                    self._apply_bridge_effect(sw, mask)
                    return self._do_split(sw, tuple(mask))
                if sw.kind == SwitchKind.HEAVY:
                    self._apply_bridge_effect(sw, mask)
                elif sw.kind == SwitchKind.SOFT:
                    self._apply_bridge_effect(sw, mask)
        else:
            for cell in (na, nb):
                sw = self.level.switch_at.get(cell)
                if sw is not None and sw.kind == SwitchKind.SOFT:
                    self._apply_bridge_effect(sw, mask)
                    # Two soft switches in one landing both fire; keep looping
                    # (toggle twice if both target same bridge).

        return State.block(na, nb, tuple(mask))

    # ---------- split cubes ----------
    def _move_cube(self, s: State, a: Action) -> State | None:
        if a not in (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT):
            return None
        dr, dc = _DELTA[a.value]
        cur = s.active_pos()
        nxt = (cur[0] + dr, cur[1] + dc)
        if not self._has_tile(nxt, s.bridges):
            return None
        if nxt in self.level.fragile:
            return None  # single cube concentrates weight
        other = s.b if s.active == 0 else s.a
        if nxt == other:
            return None  # two cubes cannot share a cell
        mask = list(s.bridges)
        # Soft switches fire for the moving cube (heavy/split never fire).
        sw = self.level.switch_at.get(nxt)
        if sw is not None and sw.kind == SwitchKind.SOFT:
            self._apply_bridge_effect(sw, mask)
        # Note: stepping a cube onto the goal is allowed but never wins.

        na, nb = (nxt, other) if s.active == 0 else (other, nxt)
        # Merge when cubes become orthogonally adjacent.
        if self._adjacent(na, nb):
            merged = State.block(na, nb, tuple(mask))
            # A merge landing on soft switch fires as a lying block too.
            # (Already fired for the moving cube; the other half firing again
            # matches "any part presses it" + toggle-on-entry.)
            extra = list(merged.bridges)
            fired = False
            for cell in merged.occupied():
                sw2 = self.level.switch_at.get(cell)
                if sw2 is not None and sw2.kind == SwitchKind.SOFT \
                        and cell != nxt:
                    self._apply_bridge_effect(sw2, extra)
                    fired = True
            if fired:
                merged = State.block(merged.a, merged.b, tuple(extra))
            return merged
        return State.split_state(na, nb, s.active, tuple(mask))

    def _apply_switch_cube(self, s: State) -> State | None:
        if not s.split:
            return None
        return State.split_state(s.a, s.b, 1 - s.active, s.bridges)

    def _do_split(self, sw, mask: tuple[bool, ...]) -> State | None:
        assert sw.split_a is not None and sw.split_b is not None
        a, b = sw.split_a, sw.split_b
        for cell in (a, b):
            if not self._has_tile(cell, mask):
                return None
            if cell in self.level.fragile:
                return None
        if a == b:
            return None
        return State.split_state(a, b, 0, mask)

    # ---------- helpers ----------
    def _apply_bridge_effect(self, sw, mask: list[bool]) -> None:
        for bid in sw.targets:
            i = self._bridge_idx.get(bid)
            if i is None:
                continue
            if sw.mode == BridgeMode.TOGGLE:
                mask[i] = not mask[i]
            elif sw.mode == BridgeMode.OPEN:
                mask[i] = True
            elif sw.mode == BridgeMode.CLOSED:
                mask[i] = False

    def _has_tile(self, cell: Coord, mask: tuple[bool, ...]) -> bool:
        r, c = cell
        lv = self.level
        if not (0 <= r < lv.rows and 0 <= c < lv.cols):
            return False
        bid = lv.bridge_at.get(cell)
        if bid is not None:
            return bool(mask[self._bridge_idx[bid]])
        ch = lv.grid[r][c]
        if ch == "-" or ch == " ":
            return False
        return True

    @staticmethod
    def _adjacent(a: Coord, b: Coord) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
