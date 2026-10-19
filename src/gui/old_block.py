# src/gui/block.py
from ursina import Entity, Vec3, color, curve, destroy, invoke, scene

from gui import old_config


class Block:
    """Quản lý hiển thị và chuyển động hoạt ảnh của khối gạch (nguyên thể và khi tách đôi)."""

    def __init__(self, start_r, start_c):
        self.entity = Entity(model="cube", color=color.orange, texture="white_cube")
        self.is_animating = False

        self.is_split = False
        self.cube1 = None
        self.cube2 = None
        self.cube1_pos = [0, 0]
        self.cube2_pos = [0, 0]
        self.active_cube_index = 1

        self.set_transform(start_r, start_c, "STANDING")

    def get_transform(self, r, c, ori):
        """Tính toán vị trí (position) và tỷ lệ (scale) 3D dựa trên tọa độ hàng, cột và hướng đặt của khối gạch."""
        if ori == "STANDING":
            return Vec3(c, 1.0, -r), Vec3(0.9, 2.0, 0.9)
        elif ori == "LYING_H":
            return Vec3(c + 0.5, 0.45, -r), Vec3(1.9, 0.9, 0.9)
        elif ori == "LYING_V":
            return Vec3(c, 0.45, -(r + 0.5)), Vec3(0.9, 0.9, 1.9)

    def set_transform(self, r, c, ori):
        """Cập nhật vị trí, kích thước và góc xoay của khối gạch nguyên thể."""
        if not self.entity:
            return
        pos, scale = self.get_transform(r, c, ori)
        self.entity.position = pos
        self.entity.scale = scale
        self.entity.rotation = Vec3(0, 0, 0)
        self.entity.color = color.orange

    def split_into_cubes(self, pos1, pos2):
        """Tách khối gạch lớn thành hai khối lập phương nhỏ độc lập tại hai vị trí chỉ định."""
        self.cleanup_split()
        self.is_split = True
        if self.entity:
            self.entity.enabled = False

        r1, c1 = pos1
        r2, c2 = pos2
        self.cube1_pos = [r1, c1]
        self.cube2_pos = [r2, c2]

        self.cube1 = Entity(
            model="cube",
            texture="white_cube",
            position=Vec3(c1, 0.45, -r1),
            scale=Vec3(0.9, 0.9, 0.9),
        )
        self.cube2 = Entity(
            model="cube",
            texture="white_cube",
            position=Vec3(c2, 0.45, -r2),
            scale=Vec3(0.9, 0.9, 0.9),
        )

        self.active_cube_index = 1
        self.update_active_cube_style()

    def get_active_cube(self):
        """Trả về entity 3D của khối gạch đang được kích hoạt điều khiển."""
        if not self.is_split:
            return self.entity
        return self.cube1 if self.active_cube_index == 1 else self.cube2

    def update_active_cube_style(self):
        """Cập nhật màu sắc để phân biệt giữa khối lập phương đang chọn và khối đang chờ khi bị tách."""
        if not self.is_split or not self.cube1 or not self.cube2:
            return

        active_color = color.rgb(29 / 255, 209 / 255, 161 / 255)
        inactive_color = color.dark_gray

        if self.active_cube_index == 1:
            self.cube1.color = active_color
            self.cube2.color = inactive_color
        else:
            self.cube1.color = inactive_color
            self.cube2.color = active_color

    def switch_active_cube(self):
        """Chuyển đổi lượt điều khiển giữa hai khối lập phương nhỏ khi ở trạng thái tách."""
        if not self.is_split or self.is_animating:
            return
        self.active_cube_index = 2 if self.active_cube_index == 1 else 1
        self.update_active_cube_style()

    def animate_cube_roll(self, cube_index, action, next_r, next_c, on_complete=None):
        """Thực hiện hoạt ảnh lăn quanh mép cho một khối lập phương nhỏ đơn lẻ."""
        self.is_animating = True
        cube = self.cube1 if cube_index == 1 else self.cube2

        if hasattr(cube, "animations"):
            cube.animations.clear()

        c = int(round(cube.x))
        r = int(round(-cube.z))

        pivot_map = {
            "RIGHT": (Vec3(c + 0.5, 0, -r), Vec3(0, 0, 90)),
            "LEFT": (Vec3(c - 0.5, 0, -r), Vec3(0, 0, -90)),
            "UP": (Vec3(c, 0, -r + 0.5), Vec3(90, 0, 0)),
            "DOWN": (Vec3(c, 0, -r - 0.5), Vec3(-90, 0, 0)),
        }
        pivot_pos, rot_axis = pivot_map[action]

        pivot = Entity(position=pivot_pos)
        cube.world_parent = pivot

        duration = old_config.ROLL_DURATION
        pivot.animate_rotation(rot_axis, duration=duration, curve=curve.in_out_quad)

        def finish():
            cube.world_parent = scene
            destroy(pivot)
            cube.position = Vec3(next_c, 0.45, -next_r)
            cube.rotation = Vec3(0, 0, 0)

            if cube_index == 1:
                self.cube1_pos = [next_r, next_c]
            else:
                self.cube2_pos = [next_r, next_c]

            self.is_animating = False
            if on_complete:
                on_complete()

        invoke(finish, delay=duration)

    def animate_cube_fall(self, cube_index, on_finish=None):
        """Thực hiện hoạt ảnh rơi xuống vực cho một khối lập phương nhỏ đơn lẻ."""
        self.is_animating = True
        cube = self.cube1 if cube_index == 1 else self.cube2
        cube.animate_position(
            cube.position + Vec3(0, -10, 0), duration=0.6, curve=curve.in_quad
        )

        def finish():
            self.is_animating = False
            if on_finish:
                on_finish()

        invoke(finish, delay=0.65)

    def merge_cubes(self, target_r, target_c, target_ori, on_complete=None):
        """Thực hiện hoạt ảnh hợp nhất hai khối lập phương nhỏ thành khối gạch lớn ban đầu."""
        self.is_animating = True
        target_pos, target_scale = self.get_transform(target_r, target_c, target_ori)

        if self.cube1:
            self.cube1.animate_position(
                target_pos, duration=0.25, curve=curve.in_out_quad
            )
        if self.cube2:
            self.cube2.animate_position(
                target_pos, duration=0.25, curve=curve.in_out_quad
            )

        def finish_merge():
            self.cleanup_split()
            self.set_transform(target_r, target_c, target_ori)
            self.is_animating = False
            if on_complete:
                on_complete()

        invoke(finish_merge, delay=0.28)

    def cleanup_split(self):
        """Hủy hai khối lập phương nhỏ và khôi phục hiển thị cho khối gạch nguyên thể."""
        if self.cube1:
            destroy(self.cube1)
            self.cube1 = None
        if self.cube2:
            destroy(self.cube2)
            self.cube2 = None
        self.is_split = False
        if hasattr(self, "entity") and self.entity:
            self.entity.enabled = True
            self.entity.color = color.orange

    def animate_roll(
        self, pivot_pos, rot_axis, next_r, next_c, next_ori, on_complete=None
    ):
        """Thực hiện hoạt ảnh lăn khối gạch nguyên thể quanh điểm xoay (pivot)."""
        self.is_animating = True

        if hasattr(self.entity, "animations"):
            self.entity.animations.clear()

        pivot = Entity(position=Vec3(*pivot_pos))
        self.entity.world_parent = pivot

        pivot.animate_rotation(
            Vec3(*rot_axis), duration=old_config.ROLL_DURATION, curve=curve.in_out_quad
        )

        def finish():
            self.entity.world_parent = scene
            destroy(pivot)
            self.set_transform(next_r, next_c, next_ori)
            self.is_animating = False
            if on_complete:
                on_complete()

        invoke(finish, delay=old_config.ROLL_DURATION)

    def animate_fall(
        self,
        level=None,
        r=0,
        c=0,
        ori="STANDING",
        bridges_mask=None,
        matrix=None,
        bridges_state=None,
        on_finish=None,
    ):
        """Thực hiện hoạt ảnh lật mép sàn và rơi xuống vực cho khối gạch khi di chuyển ra ngoài phạm vi hợp lệ."""
        self.is_animating = True

        def is_solid(tr, tc):
            if level is not None:
                if tr < 0 or tr >= level.rows or tc < 0 or tc >= level.cols:
                    return False
                ch = level.grid[tr][tc]
                if ch in ("-", " "):
                    return False
                bid = level.bridge_at.get((tr, tc))
                if bid is not None and bridges_mask is not None:
                    idx = (
                        level.bridge_order.index(bid)
                        if bid in level.bridge_order
                        else -1
                    )
                    if idx != -1 and not bridges_mask[idx]:
                        return False
                return True
            elif matrix is not None:
                if tr < 0 or tr >= len(matrix) or tc < 0 or tc >= len(matrix[0]):
                    return False
                val = matrix[tr][tc]
                if val in ("-", " "):
                    return False
                if (
                    val.upper() == "B"
                    and bridges_state
                    and not bridges_state.get((tr, tc), False)
                ):
                    return False
                return True
            return False

        pivot_pos = None
        rot_offset = Vec3(0, 0, 0)

        if ori == "LYING_H":
            left_solid = is_solid(r, c)
            right_solid = is_solid(r, c + 1)

            if left_solid and not right_solid:
                pivot_pos = Vec3(c + 0.5, 0, -r)
                rot_offset = Vec3(0, 0, 90)
            elif not left_solid and right_solid:
                pivot_pos = Vec3(c + 0.5, 0, -r)
                rot_offset = Vec3(0, 0, -90)

        elif ori == "LYING_V":
            top_solid = is_solid(r, c)
            bottom_solid = is_solid(r + 1, c)

            if top_solid and not bottom_solid:
                pivot_pos = Vec3(c, 0, -(r + 0.5))
                rot_offset = Vec3(-90, 0, 0)
            elif not top_solid and bottom_solid:
                pivot_pos = Vec3(c, 0, -(r + 0.5))
                rot_offset = Vec3(90, 0, 0)

        if pivot_pos is not None:
            pivot = Entity(position=pivot_pos)
            self.entity.world_parent = pivot

            pivot.animate_rotation(rot_offset, duration=0.2, curve=curve.in_quad)

            def drop_down():
                pivot.animate_position(
                    pivot.position + Vec3(0, -10, 0), duration=0.5, curve=curve.in_quad
                )

                def finish():
                    self.entity.world_parent = scene
                    destroy(pivot)
                    self.is_animating = False
                    if on_finish:
                        on_finish()

                invoke(finish, delay=0.55)

            invoke(drop_down, delay=0.2)

        else:
            self.entity.animate_position(
                self.entity.position + Vec3(0, -10, 0),
                duration=0.6,
                curve=curve.in_quad,
            )

            def finish_free_fall():
                self.is_animating = False
                if on_finish:
                    on_finish()

            invoke(finish_free_fall, delay=0.65)

    def animate_win(self, on_finish=None):
        """Thực hiện hoạt ảnh thu nhỏ và lọt hố khi khối gạch hoàn thành level."""
        self.is_animating = True
        duration = 0.45

        self.entity.animate_position(
            Vec3(self.entity.x, -0.2, self.entity.z),
            duration=duration,
            curve=curve.in_quad,
        )
        self.entity.animate_scale(
            Vec3(0.85, 0.0, 0.85), duration=duration, curve=curve.in_quad
        )

        def hide_block():
            self.entity.enabled = False
            self.is_animating = False
            if on_finish:
                on_finish()

        invoke(hide_block, delay=duration + 0.02)

    def animate_exit_fly_up(self, duration=0.35, on_complete=None):
        """Thực hiện hoạt ảnh khối gạch bay vút lên trên khi chọn lại hoặc chuyển màn chơi."""
        self.is_animating = True

        if self.is_split:
            if self.cube1:
                self.cube1.animate_position(
                    self.cube1.position + Vec3(0, 15, 0),
                    duration=duration,
                    curve=curve.in_back,
                )
            if self.cube2:
                self.cube2.animate_position(
                    self.cube2.position + Vec3(0, 15, 0),
                    duration=duration,
                    curve=curve.in_back,
                )
        else:
            if hasattr(self, "entity") and self.entity:
                self.entity.animate_position(
                    self.entity.position + Vec3(0, 15, 0),
                    duration=duration,
                    curve=curve.in_back,
                )

        def finish():
            self.is_animating = False
            if on_complete:
                on_complete()

        invoke(finish, delay=duration)

    def animate_drop_in(self, target_r, target_c, delay=0.0, on_complete=None):
        """Thực hiện hoạt ảnh khối gạch thả rơi từ trên cao xuống sàn khi bắt đầu chơi."""
        self.is_animating = True
        target_pos, target_scale = self.get_transform(target_r, target_c, "STANDING")

        self.entity.position = Vec3(target_pos.x, 12.0, target_pos.z)
        self.entity.scale = target_scale
        self.entity.rotation = Vec3(0, 0, 0)
        self.entity.color = color.orange

        drop_duration = 0.55

        def start_drop():
            self.entity.enabled = True
            self.entity.animate_position(
                target_pos, duration=drop_duration, curve=curve.out_bounce
            )

            def finish():
                if hasattr(self.entity, "animations"):
                    self.entity.animations.clear()

                self.entity.position = target_pos
                self.entity.rotation = Vec3(0, 0, 0)
                self.is_animating = False

                if on_complete:
                    invoke(on_complete, delay=0.08)

            invoke(finish, delay=drop_duration)

        if delay > 0:
            self.entity.enabled = False
            invoke(start_drop, delay=delay)
        else:
            start_drop()

    def destroy_block(self):
        """Hủy tất cả các entity 3D thuộc về khối gạch để giải phóng tài nguyên."""
        if self.cube1:
            destroy(self.cube1)
            self.cube1 = None
        if self.cube2:
            destroy(self.cube2)
            self.cube2 = None
        self.is_split = False

        if hasattr(self, "entity") and self.entity:
            destroy(self.entity)
            self.entity = None
