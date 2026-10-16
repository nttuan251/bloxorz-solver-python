# src/gui/board.py
import random
from ursina import Entity, Vec3, destroy, invoke, curve, color
from src.gui import config

class Board:
    def __init__(self, level, animate_entrance=True, start_delay=0.6):
        """
        start_delay: Thời gian hoãn (giây) trước khi bắt đầu chạy hoạt ảnh trồi lên.
        """
        self.level = level
        self.tiles = {}
        self.bridge_entities = {}
        self.switch_bases = []
        self.start_delay = start_delay
        self.tile_duration = 0.5  # Thời gian trồi của mỗi ô
        self.step_delay = 0.035   # Độ trễ giữa các ô
        self._build_board(animate_entrance=animate_entrance, start_delay=start_delay)

    def _build_board(self, animate_entrance=True, start_delay=0.6):
        for r in range(self.level.rows):
            for c in range(self.level.cols):
                ch = self.level.grid[r][c]
                if ch in ('-', ' '):
                    continue

                tile_info = config.TILE_CONFIGS.get(ch, config.TILE_CONFIGS['o'])
                target_y = tile_info['y']
                target_pos = Vec3(c, target_y, -r)

                # 1. Đế công tắc
                if ch in ('s', 'h', 'p'):
                    base_y = -0.1
                    start_base_y = -6.1 if animate_entrance else base_y
                    base = Entity(
                        model='cube',
                        color=config.TILE_CONFIGS['o']['color'],
                        texture='white_cube',
                        position=Vec3(c, start_base_y, -r),
                        scale=config.TILE_SCALE
                    )
                    if animate_entrance:
                        delay_time = self.start_delay + (r + c) * self.step_delay
                        base.animate_position(Vec3(c, base_y, -r), duration=0.6, delay=delay_time, curve=curve.out_back)
                    self.switch_bases.append(base)

                # 2. Tạo Entity cho ô sàn
                start_y = (target_y - 6.0) if animate_entrance else target_y
                tile_entity = Entity(
                    model=tile_info['model'],
                    color=tile_info['color'],
                    texture=tile_info.get('texture', 'white_cube'),
                    position=Vec3(c, start_y, -r),
                    scale=tile_info['scale'],
                    rotation=tile_info.get('rotation', Vec3(0, 0, 0)),
                    double_sided=True
                )

                delay_time = self.start_delay + (r + c) * self.step_delay

                if ch == 'b':
                    tile_entity.enabled = False
                    self.bridge_entities[(r, c)] = tile_entity
                else:
                    if animate_entrance:
                        tile_entity.animate_position(
                            target_pos,
                            duration=self.tile_duration,
                            delay=delay_time,
                            curve=curve.out_back
                        )
                    self.tiles[(r, c)] = tile_entity

    def sync_bridges(self, bridges_mask):
        """Đồng bộ ẩn/hiện Cầu theo mảng boolean mask từ core State"""
        for i, bid in enumerate(self.level.bridge_order):
            is_open = bridges_mask[i]
            group = self.level.bridge_groups[bid]
            for cell in group.cells:
                if cell in self.bridge_entities:
                    entity = self.bridge_entities[cell]
                    r, c = cell
                    target_y = config.TILE_CONFIGS['b']['y']
                    target_pos = Vec3(c, target_y, -r)

                    if is_open:
                        if not entity.enabled:
                            entity.enabled = True
                            entity.position = Vec3(c, target_y - 1.5, -r)
                            entity.animate_position(target_pos, duration=0.4, curve=curve.out_back)
                    else:
                        if entity.enabled:
                            entity.animate_position(Vec3(c, target_y - 1.5, -r), duration=0.25, curve=curve.in_quad)
                            def hide(e=entity):
                                e.enabled = False
                            invoke(hide, delay=0.26)

    def animate_break_tile(self, r, c):
        if (r, c) not in self.tiles:
            return
        tile = self.tiles.pop((r, c))
        tile_pos = tile.position
        tile_color = tile.color
        destroy(tile)

        debris_list = []
        for _ in range(8):
            offset_x = random.uniform(-0.3, 0.3)
            offset_z = random.uniform(-0.3, 0.3)
            debris = Entity(
                model='cube', color=tile_color, texture='white_cube',
                position=tile_pos + Vec3(offset_x, 0, offset_z), scale=Vec3(0.25, 0.25, 0.25)
            )
            target_x = tile_pos.x + offset_x * 2.5
            target_z = tile_pos.z + offset_z * 2.5
            target_y = tile_pos.y - 4.0
            debris.animate_position(Vec3(target_x, target_y, target_z), duration=0.5, curve=curve.in_quad)
            debris.animate_rotation(Vec3(random.randint(90, 360), random.randint(90, 360), random.randint(90, 360)), duration=0.5)
            debris.animate_scale(Vec3(0, 0, 0), duration=0.5, curve=curve.in_quad)
            debris_list.append(debris)

        invoke(lambda: [destroy(d) for d in debris_list], delay=0.55)

    def reset(self, animate_entrance=False):
        for r in range(self.level.rows):
            for c in range(self.level.cols):
                ch = self.level.grid[r][c]
                if ch not in ('-', ' ') and (r, c) not in self.tiles and ch != 'b':
                    tile_info = config.TILE_CONFIGS.get(ch, config.TILE_CONFIGS['o'])
                    tile_entity = Entity(
                        model='cube', color=tile_info['color'], texture=tile_info.get('texture', 'white_cube'),
                        position=Vec3(c, tile_info['y'], -r), scale=tile_info['scale'],
                        rotation=tile_info.get('rotation', Vec3(0, 0, 0)), double_sided=True
                    )
                    self.tiles[(r, c)] = tile_entity

    def get_entrance_duration(self):
        max_rc = 0
        for r in range(self.level.rows):
            for c in range(self.level.cols):
                if self.level.grid[r][c] not in ('-', ' '):
                    max_rc = max(max_rc, r + c)
        return self.start_delay + max_rc * self.step_delay + self.tile_duration