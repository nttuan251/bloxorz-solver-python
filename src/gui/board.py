"""3D board built from a core Level. Handles bridge open/close refresh."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ursina import Entity, Vec3

import config as config
from core.level import Level


class Board:
    def __init__(self, level: Level):
        self.level = level
        self.tiles: dict[tuple[int, int], Entity] = {}
        self.markers: list[Entity] = []
        self._build()

    # ---------- build ----------
    def _base_color(self, r: int, c: int):
        lv = self.level
        ch = lv.grid[r][c]
        if ch == '-' or ch == ' ':
            if (r, c) in lv.bridge_at:
                return config.TILE_COLORS['bridge_open']
            return None
        if (r, c) in lv.bridge_at:
            return config.TILE_COLORS['bridge_open']
        if ch == 'S':
            return config.TILE_COLORS['start']
        if ch == 'T':
            return config.TILE_COLORS['goal']
        if ch == 'f':
            return config.TILE_COLORS['fragile']
        # Special tiles get a tinted base so they read instantly (marker alone
        # is too small at follow-cam distance).
        sw = lv.switch_at.get((r, c))
        if sw is not None:
            kind = sw.kind.value  # soft | heavy | split
            return config.TILE_COLORS.get(f'{kind}_base',
                                          config.TILE_COLORS['floor'])
        if ch in ('A', 'B'):
            return config.TILE_COLORS['dest_base']
        # o / . / s / h / p leftover are plain floor
        return config.TILE_COLORS['floor']

    def _build(self):
        from core.tile import SwitchKind
        lv = self.level
        for r in range(lv.rows):
            for c in range(lv.cols):
                col = self._base_color(r, c)
                if col is None:
                    continue
                t = Entity(model='cube', color=col,
                           position=Vec3(c, 0, -r), scale=config.TILE_SCALE)
                self.tiles[(r, c)] = t
        # Switch / dest markers (small props above the tile).
        for sw in lv.switches:
            r, c = sw.pos
            if (r, c) not in self.tiles:
                continue
            mc = config.SWITCH_COLORS[sw.kind.value]
            if sw.kind == SwitchKind.SOFT:
                m = Entity(model='cylinder', color=mc,
                           position=Vec3(c, 0.25, -r), scale=(0.55, 0.3, 0.55))
            elif sw.kind == SwitchKind.HEAVY:
                m = Entity(model='cube', color=mc, rotation=(0, 45, 0),
                           position=Vec3(c, 0.28, -r), scale=(0.5, 0.35, 0.5))
            else:  # SPLIT "( )" - two white posts
                m = Entity(model='cube', color=mc,
                           position=Vec3(c - 0.2, 0.28, -r), scale=(0.24, 0.36, 0.55))
                m2 = Entity(model='cube', color=mc,
                            position=Vec3(c + 0.2, 0.28, -r), scale=(0.24, 0.36, 0.55))
                self.markers.append(m2)
            self.markers.append(m)
        # A/B destinations: teal base + larger white diamonds.
        for r in range(lv.rows):
            for c in range(lv.cols):
                if lv.grid[r][c] in ('A', 'B'):
                    self.markers.append(Entity(
                        model='cube', color=config.SWITCH_COLORS['dest'],
                        rotation=(0, 45, 0),
                        position=Vec3(c, 0.24, -r), scale=(0.42, 0.2, 0.42)))

    # ---------- runtime ----------
    def refresh(self, state) -> None:
        """Show/hide bridge tiles from the bridge mask in `state`."""
        if not self.level.bridge_order:
            return
        idx = {bid: i for i, bid in enumerate(self.level.bridge_order)}
        for (r, c), bid in self.level.bridge_at.items():
            ent = self.tiles.get((r, c))
            if ent is None:
                continue
            is_open = bool(state.bridges[idx[bid]]) if state is not None else False
            ent.enabled = True  # keep visible; closed = faint ghost
            ent.color = (config.TILE_COLORS['bridge_open'] if is_open
                         else config.TILE_COLORS['bridge_closed'])

    def destroy(self):
        from ursina import destroy
        for e in list(self.tiles.values()):
            destroy(e)
        for m in self.markers:
            destroy(m)
        self.tiles.clear()
        self.markers.clear()
