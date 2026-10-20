from __future__ import annotations

import random
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

from ursina import Entity, Vec3, color, curve, destroy, invoke
from ursina.color import rgb

from src.game.core.tile import TileType
from src.gui import config

if TYPE_CHECKING:
    from src.game.core.level import Level

Coordinate = tuple[int, int]

SWITCH_TILE_TYPES = frozenset(
    {TileType.SOFT_SWITCH, TileType.HEAVY_SWITCH, TileType.SPLIT_SWITCH}
)

SPAWN_DEPTH = 6.0
BRIDGE_HIDDEN_DEPTH = 1.5
SWITCH_BASE_Y = -0.1
FALL_DISTANCE = 12.0
FALL_DURATION = 0.45
FALL_STEP_DELAY = 0.02


def _rgb255(r: int, g: int, b: int) -> color.Color:
    return rgb(r / 255, g / 255, b / 255)


DEFAULT_BRIDGE_COLOR = _rgb255(84, 160, 255)
BRIDGE_COLOR_BY_SWITCH: dict[TileType, color.Color] = {
    TileType.SOFT_SWITCH: _rgb255(255, 107, 129),
    TileType.HEAVY_SWITCH: _rgb255(84, 160, 255),
    TileType.SPLIT_SWITCH: _rgb255(29, 209, 161),
}


def _world_pos(coord: Coordinate, y: float) -> Vec3:
    row, col = coord
    return Vec3(col, y, -row)


def _transparent(col: color.Color) -> color.Color:
    return color.rgba(col.r, col.g, col.b, 0)


class Board:
    def __init__(
        self, level: Level, animate_entrance: bool = True, start_delay: float = 0.6
    ) -> None:
        self.level = level
        self.start_delay = start_delay
        self.tile_duration = 0.5
        self.step_delay = 0.035

        self.tiles: dict[Coordinate, Entity] = {}
        self.bridge_entities: dict[Coordinate, Entity] = {}
        self.switch_bases: list[Entity] = []

        level_map = level.get_map()
        self.rows = max((r for r, _ in level_map), default=0) + 1
        self.cols = max((c for _, c in level_map), default=0) + 1

        self._bridge_colors = self._compute_bridge_colors()
        self._build_board(animate_entrance)

    def _compute_bridge_colors(self) -> dict[Coordinate, color.Color]:
        level_map = self.level.get_map()
        colors: dict[Coordinate, color.Color] = {}
        for coord, tile_type in level_map.items():
            if tile_type not in SWITCH_TILE_TYPES:
                continue
            for (
                bridge_coord,
                _,
            ) in self.level.get_associated_coords_and_actions_from_switch(coord):
                colors.setdefault(bridge_coord, BRIDGE_COLOR_BY_SWITCH[tile_type])
        return colors

    def _bridge_color(self, coord: Coordinate) -> color.Color:
        return self._bridge_colors.get(coord, DEFAULT_BRIDGE_COLOR)

    @staticmethod
    def _tile_config(tile_type: TileType) -> dict:
        return config.TILE_CONFIGS.get(tile_type, config.TILE_CONFIGS[TileType.NORMAL])

    def _entrance_delay(self, coord: Coordinate) -> float:
        row, col = coord
        return self.start_delay + (row + col) * self.step_delay

    @staticmethod
    def _rise(
        entity: Entity,
        position: Vec3,
        target_color: color.Color,
        delay: float,
        duration: float,
    ) -> None:
        entity.animate_position(
            position, duration=duration, delay=delay, curve=curve.out_back
        )
        entity.animate_color(
            target_color, duration=duration, delay=delay, curve=curve.out_back
        )

    def _build_board(self, animate_entrance: bool) -> None:
        for coord, tile_type in self.level.get_map().items():
            if tile_type in SWITCH_TILE_TYPES:
                self.switch_bases.append(
                    self._spawn_switch_base(coord, animate_entrance)
                )

            entity = self._spawn_tile(coord, tile_type, animate_entrance)
            if tile_type == TileType.BRIDGE:
                self.bridge_entities[coord] = entity
            else:
                self.tiles[coord] = entity

    def _spawn_tile(
        self, coord: Coordinate, tile_type: TileType, animate: bool
    ) -> Entity:
        cfg = self._tile_config(tile_type)
        is_bridge = tile_type == TileType.BRIDGE
        target_color = self._bridge_color(coord) if is_bridge else cfg["color"]
        target_pos = _world_pos(coord, cfg["y"])
        rises = animate and not is_bridge

        entity = Entity(
            model=cfg["model"],
            color=_transparent(target_color) if rises else target_color,
            texture=cfg.get("texture", "white_cube"),
            position=target_pos - Vec3(0, SPAWN_DEPTH, 0) if rises else target_pos,
            scale=cfg["scale"],
            rotation=cfg.get("rotation", Vec3(0, 0, 0)),
            double_sided=True,
            enabled=not is_bridge,
        )
        if rises:
            self._rise(
                entity,
                target_pos,
                target_color,
                self._entrance_delay(coord),
                self.tile_duration,
            )
        return entity

    def _spawn_switch_base(self, coord: Coordinate, animate: bool) -> Entity:
        base_color = config.TILE_CONFIGS[TileType.NORMAL]["color"]
        target_pos = _world_pos(coord, SWITCH_BASE_Y)

        base = Entity(
            model="cube",
            color=_transparent(base_color) if animate else base_color,
            texture="white_cube",
            position=target_pos - Vec3(0, SPAWN_DEPTH, 0) if animate else target_pos,
            scale=config.TILE_SCALE,
        )
        if animate:
            self._rise(base, target_pos, base_color, self._entrance_delay(coord), 0.6)
        return base

    def sync_bridges(
        self, bridges_mask: dict[Coordinate, bool], animate_entrance: bool = False
    ) -> None:
        for coord, is_open in bridges_mask.items():
            entity = self.bridge_entities.get(coord)
            if entity is None:
                continue
            if is_open and not entity.enabled:
                self._show_bridge(coord, entity, animate_entrance)
            elif not is_open and entity.enabled:
                self._hide_bridge(coord, entity)

    def _show_bridge(
        self, coord: Coordinate, entity: Entity, animate_entrance: bool
    ) -> None:
        target_pos = _world_pos(coord, config.TILE_CONFIGS[TileType.BRIDGE]["y"])
        target_color = self._bridge_color(coord)
        entity.enabled = True

        if animate_entrance:
            entity.position = target_pos - Vec3(0, SPAWN_DEPTH, 0)
            entity.color = _transparent(target_color)
            self._rise(
                entity,
                target_pos,
                target_color,
                self._entrance_delay(coord),
                self.tile_duration,
            )
        else:
            entity.color = target_color
            entity.position = target_pos - Vec3(0, BRIDGE_HIDDEN_DEPTH, 0)
            entity.animate_position(target_pos, duration=0.4, curve=curve.out_back)

    @staticmethod
    def _hide_bridge(coord: Coordinate, entity: Entity) -> None:
        hidden_pos = _world_pos(
            coord, config.TILE_CONFIGS[TileType.BRIDGE]["y"] - BRIDGE_HIDDEN_DEPTH
        )
        entity.animate_position(hidden_pos, duration=0.25, curve=curve.in_quad)
        invoke(setattr, entity, "enabled", False, delay=0.26)

    def animate_break_tile(self, r: int, c: int) -> None:
        tile = self.tiles.pop((r, c), None)
        if tile is None:
            return

        origin, tile_color = tile.position, tile.color
        destroy(tile)

        debris_list = []
        for _ in range(8):
            dx, dz = random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)
            debris = Entity(
                model="cube",
                color=tile_color,
                texture="white_cube",
                position=origin + Vec3(dx, 0, dz),
                scale=Vec3(0.25),
            )
            debris.animate_position(
                Vec3(origin.x + dx * 2.5, origin.y - 4.0, origin.z + dz * 2.5),
                duration=0.5,
                curve=curve.in_quad,
            )
            debris.animate_rotation(
                Vec3(*(random.randint(90, 360) for _ in range(3))), duration=0.5
            )
            debris.animate_scale(Vec3(0), duration=0.5, curve=curve.in_quad)
            debris_list.append(debris)

        invoke(lambda: [destroy(d) for d in debris_list], delay=0.55)

    def reset(self, animate_entrance: bool = False) -> None:
        for coord, tile_type in self.level.get_map().items():
            if tile_type != TileType.BRIDGE and coord not in self.tiles:
                self.tiles[coord] = self._spawn_tile(coord, tile_type, animate_entrance)

    def get_entrance_duration(self) -> float:
        max_diagonal = max((r + c for r, c in self.level.get_map()), default=0)
        return self.start_delay + max_diagonal * self.step_delay + self.tile_duration

    def animate_exit_fall_down(
        self,
        pause_duration: float = 0.35,
        on_complete: Callable[[], None] | None = None,
    ) -> float:
        max_delay = 0.0
        for (r, c), entity in self._iter_visible_entities():
            delay = (r + c) * FALL_STEP_DELAY
            max_delay = max(max_delay, delay)
            entity.animate_position(
                Vec3(entity.x, entity.y - FALL_DISTANCE, entity.z),
                duration=FALL_DURATION,
                delay=delay,
                curve=curve.in_back,
            )
            entity.animate_color(
                _transparent(entity.color),
                duration=FALL_DURATION,
                delay=delay,
                curve=curve.in_back,
            )

        total_time = max_delay + FALL_DURATION + pause_duration
        if on_complete:
            invoke(on_complete, delay=total_time)
        return total_time

    def _iter_visible_entities(self) -> Iterator[tuple[Coordinate, Entity]]:
        yield from self.tiles.items()
        yield from (
            (coord, b) for coord, b in self.bridge_entities.items() if b.enabled
        )
        for base in self.switch_bases:
            yield (round(-base.z), round(base.x)), base

    def destroy_board(self) -> None:
        for entity in (
            *self.tiles.values(),
            *self.bridge_entities.values(),
            *self.switch_bases,
        ):
            destroy(entity)
        self.tiles.clear()
        self.bridge_entities.clear()
        self.switch_bases.clear()
