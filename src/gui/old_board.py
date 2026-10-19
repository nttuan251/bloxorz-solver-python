# src/gui/board.py
import random

from ursina import Entity, Vec3, color, curve, destroy, invoke

from gui import old_config


class Board:
    """Quản lý khởi tạo, hiển thị và các hiệu ứng hoạt ảnh cho bàn chơi (ô sàn, cầu, đế công tắc)."""

    def __init__(self, level, animate_entrance=True, start_delay=0.6):
        self.level = level
        self.tiles = {}
        self.bridge_entities = {}
        self.switch_bases = []
        self.start_delay = start_delay
        self.tile_duration = 0.5
        self.step_delay = 0.035
        self._build_board(animate_entrance=animate_entrance, start_delay=start_delay)

    def _get_bridge_color(self, bid):
        """Xác định màu sắc của đoạn cầu dựa trên loại công tắc điều khiển tương ứng."""
        default_color = color.rgb(84 / 255, 160 / 255, 255 / 255)

        if hasattr(self.level, "switches"):
            switches = self.level.switches
            sw_list = switches.values() if isinstance(switches, dict) else switches

            for sw in sw_list:
                stype = ""
                for attr in ["type", "stype", "kind", "switch_type", "mode"]:
                    val = (
                        getattr(sw, attr, None)
                        if not isinstance(sw, dict)
                        else sw.get(attr)
                    )
                    if val:
                        stype = str(val).lower()
                        break

                targets = None
                for attr in ["targets", "bridges", "bridge_ids", "target_bridges"]:
                    val = (
                        getattr(sw, attr, None)
                        if not isinstance(sw, dict)
                        else sw.get(attr)
                    )
                    if val is not None:
                        targets = val
                        break

                is_target = False
                if targets is not None:
                    if isinstance(targets, (list, tuple, set)):
                        for t in targets:
                            if t == bid:
                                is_target = True
                                break
                            elif (
                                isinstance(t, (list, tuple))
                                and len(t) > 0
                                and t[0] == bid
                            ):
                                is_target = True
                                break
                            elif (
                                hasattr(t, "bridge_id")
                                and getattr(t, "bridge_id") == bid
                            ):
                                is_target = True
                                break
                    elif isinstance(targets, dict):
                        if bid in targets:
                            is_target = True
                    elif targets == bid:
                        is_target = True

                if is_target:
                    if "soft" in stype or stype in ("s", "soft"):
                        return color.rgb(255 / 255, 107 / 255, 129 / 255)
                    elif "heavy" in stype or stype in ("h", "heavy"):
                        return color.rgb(84 / 255, 160 / 255, 255 / 255)
                    elif "split" in stype or stype in ("p", "split"):
                        return color.rgb(29 / 255, 209 / 255, 161 / 255)

        return default_color

    def _build_board(self, animate_entrance=True, start_delay=0.6):
        """Dựng các đối tượng 3D cho các ô sàn, cầu và đế công tắc trên bàn chơi."""
        for r in range(self.level.rows):
            for c in range(self.level.cols):
                ch = self.level.grid[r][c]
                if ch in ("-", " "):
                    continue

                tile_info = old_config.TILE_CONFIGS.get(
                    ch, old_config.TILE_CONFIGS["o"]
                )
                target_y = tile_info["y"]
                target_pos = Vec3(c, target_y, -r)

                if ch == "b":
                    bid = self.level.bridge_at.get((r, c))
                    target_color = (
                        self._get_bridge_color(bid)
                        if bid
                        else old_config.TILE_CONFIGS["b"]["color"]
                    )
                    start_color = target_color
                else:
                    target_color = tile_info["color"]
                    start_color = (
                        color.rgba(target_color.r, target_color.g, target_color.b, 0)
                        if animate_entrance
                        else target_color
                    )

                if ch in ("s", "h", "p"):
                    base_y = -0.1
                    start_base_y = -6.1 if animate_entrance else base_y
                    base_target_color = old_config.TILE_CONFIGS["o"]["color"]
                    base_start_color = (
                        color.rgba(
                            base_target_color.r,
                            base_target_color.g,
                            base_target_color.b,
                            0,
                        )
                        if animate_entrance
                        else base_target_color
                    )

                    base = Entity(
                        model="cube",
                        color=base_start_color,
                        texture="white_cube",
                        position=Vec3(c, start_base_y, -r),
                        scale=old_config.TILE_SCALE,
                    )
                    if animate_entrance:
                        delay_time = self.start_delay + (r + c) * self.step_delay
                        base.animate_position(
                            Vec3(c, base_y, -r),
                            duration=0.6,
                            delay=delay_time,
                            curve=curve.out_back,
                        )
                        base.animate_color(
                            base_target_color,
                            duration=0.6,
                            delay=delay_time,
                            curve=curve.out_back,
                        )
                    self.switch_bases.append(base)

                start_y = (target_y - 6.0) if animate_entrance else target_y
                tile_entity = Entity(
                    model=tile_info["model"],
                    color=start_color,
                    texture=tile_info.get("texture", "white_cube"),
                    position=Vec3(c, start_y, -r),
                    scale=tile_info["scale"],
                    rotation=tile_info.get("rotation", Vec3(0, 0, 0)),
                    double_sided=True,
                )

                delay_time = self.start_delay + (r + c) * self.step_delay

                if ch == "b":
                    tile_entity.enabled = False
                    self.bridge_entities[(r, c)] = tile_entity
                else:
                    if animate_entrance:
                        tile_entity.animate_position(
                            target_pos,
                            duration=self.tile_duration,
                            delay=delay_time,
                            curve=curve.out_back,
                        )
                        tile_entity.animate_color(
                            target_color,
                            duration=self.tile_duration,
                            delay=delay_time,
                            curve=curve.out_back,
                        )
                    self.tiles[(r, c)] = tile_entity

    def sync_bridges(self, bridges_mask, animate_entrance=False):
        """Cập nhật trạng thái ẩn/hiện và hoạt ảnh nâng/hạ của các đoạn cầu theo trạng thái công tắc."""
        for i, bid in enumerate(self.level.bridge_order):
            is_open = bridges_mask[i]
            group = self.level.bridge_groups[bid]
            target_color = self._get_bridge_color(bid)

            for cell in group.cells:
                if cell in self.bridge_entities:
                    entity = self.bridge_entities[cell]
                    r, c = cell
                    target_y = old_config.TILE_CONFIGS["b"]["y"]
                    target_pos = Vec3(c, target_y, -r)

                    if is_open:
                        if not entity.enabled:
                            entity.enabled = True
                            if animate_entrance:
                                delay_time = (
                                    self.start_delay + (r + c) * self.step_delay
                                )
                                entity.position = Vec3(c, target_y - 6.0, -r)
                                entity.color = color.rgba(
                                    target_color.r, target_color.g, target_color.b, 0
                                )
                                entity.animate_position(
                                    target_pos,
                                    duration=self.tile_duration,
                                    delay=delay_time,
                                    curve=curve.out_back,
                                )
                                entity.animate_color(
                                    target_color,
                                    duration=self.tile_duration,
                                    delay=delay_time,
                                    curve=curve.out_back,
                                )
                            else:
                                entity.color = target_color
                                entity.position = Vec3(c, target_y - 1.5, -r)
                                entity.animate_position(
                                    target_pos, duration=0.4, curve=curve.out_back
                                )
                    else:
                        if entity.enabled:
                            entity.animate_position(
                                Vec3(c, target_y - 1.5, -r),
                                duration=0.25,
                                curve=curve.in_quad,
                            )

                            def hide(e=entity):
                                e.enabled = False

                            invoke(hide, delay=0.26)

    def animate_break_tile(self, r, c):
        """Thực hiện hiệu ứng ô sàn vỡ thành nhiều mảnh nhỏ văng ra khi bị khối gạch giẫm lên."""
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
                model="cube",
                color=tile_color,
                texture="white_cube",
                position=tile_pos + Vec3(offset_x, 0, offset_z),
                scale=Vec3(0.25, 0.25, 0.25),
            )
            target_x = tile_pos.x + offset_x * 2.5
            target_z = tile_pos.z + offset_z * 2.5
            target_y = tile_pos.y - 4.0
            debris.animate_position(
                Vec3(target_x, target_y, target_z), duration=0.5, curve=curve.in_quad
            )
            debris.animate_rotation(
                Vec3(
                    random.randint(90, 360),
                    random.randint(90, 360),
                    random.randint(90, 360),
                ),
                duration=0.5,
            )
            debris.animate_scale(Vec3(0, 0, 0), duration=0.5, curve=curve.in_quad)
            debris_list.append(debris)

        invoke(lambda: [destroy(d) for d in debris_list], delay=0.55)

    def reset(self, animate_entrance=False):
        """Khôi phục lại các ô sàn đã bị vỡ về vị trí và trạng thái ban đầu."""
        for r in range(self.level.rows):
            for c in range(self.level.cols):
                ch = self.level.grid[r][c]
                if ch not in ("-", " ") and (r, c) not in self.tiles and ch != "b":
                    tile_info = old_config.TILE_CONFIGS.get(
                        ch, old_config.TILE_CONFIGS["o"]
                    )
                    tile_entity = Entity(
                        model="cube",
                        color=tile_info["color"],
                        texture=tile_info.get("texture", "white_cube"),
                        position=Vec3(c, tile_info["y"], -r),
                        scale=tile_info["scale"],
                        rotation=tile_info.get("rotation", Vec3(0, 0, 0)),
                        double_sided=True,
                    )
                    self.tiles[(r, c)] = tile_entity

    def get_entrance_duration(self):
        """Tính toán tổng thời gian hoàn tất hiệu ứng mọc sàn khi bắt đầu level."""
        max_rc = 0
        for r in range(self.level.rows):
            for c in range(self.level.cols):
                if self.level.grid[r][c] not in ("-", " "):
                    max_rc = max(max_rc, r + c)
        return self.start_delay + max_rc * self.step_delay + self.tile_duration

    def animate_exit_fall_down(self, pause_duration=0.35, on_complete=None):
        """Thực hiện hiệu ứng toàn bộ ô sàn và cầu rơi xuống vực khi chuyển sang màn chơi mới."""
        max_delay = 0.0
        fall_distance = 12.0
        duration = 0.45

        for (r, c), tile in self.tiles.items():
            delay = (r + c) * 0.02
            max_delay = max(max_delay, delay)
            fade_color = color.rgba(tile.color.r, tile.color.g, tile.color.b, 0)

            tile.animate_position(
                Vec3(tile.x, tile.y - fall_distance, tile.z),
                duration=duration,
                delay=delay,
                curve=curve.in_back,
            )
            tile.animate_color(
                fade_color, duration=duration, delay=delay, curve=curve.in_back
            )

        for (r, c), bridge in self.bridge_entities.items():
            if bridge.enabled:
                delay = (r + c) * 0.02
                max_delay = max(max_delay, delay)
                fade_color = color.rgba(
                    bridge.color.r, bridge.color.g, bridge.color.b, 0
                )

                bridge.animate_position(
                    Vec3(bridge.x, bridge.y - fall_distance, bridge.z),
                    duration=duration,
                    delay=delay,
                    curve=curve.in_back,
                )
                bridge.animate_color(
                    fade_color, duration=duration, delay=delay, curve=curve.in_back
                )

        for base in self.switch_bases:
            c = int(round(base.x))
            r = int(round(-base.z))
            delay = (r + c) * 0.02
            max_delay = max(max_delay, delay)
            fade_color = color.rgba(base.color.r, base.color.g, base.color.b, 0)

            base.animate_position(
                Vec3(base.x, base.y - fall_distance, base.z),
                duration=duration,
                delay=delay,
                curve=curve.in_back,
            )
            base.animate_color(
                fade_color, duration=duration, delay=delay, curve=curve.in_back
            )

        total_time = max_delay + duration + pause_duration
        if on_complete:
            invoke(on_complete, delay=total_time)
        return total_time

    def destroy_board(self):
        """Hủy tất cả các entity 3D của ô sàn, cầu và đế công tắc để giải phóng tài nguyên."""
        for tile in list(self.tiles.values()):
            destroy(tile)
        self.tiles.clear()

        for bridge in list(self.bridge_entities.values()):
            destroy(bridge)
        self.bridge_entities.clear()

        for base in list(self.switch_bases):
            destroy(base)
        self.switch_bases.clear()
