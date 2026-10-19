# src/gui/controller.py
import threading
from pathlib import Path

from src.core.game import BloxorzGame
from src.core.loader import load_level
from src.core.tile import Action
from src.solvers import SOLVERS
from ursina import Entity, Vec3, camera, color, held_keys, invoke, lerp, mouse, time

import gui.old_config as old_config
from gui.old_block import Block
from gui.old_board import Board
from gui.ui import HUD


class GameController:
    """Điều phối chính toàn bộ luồng tương tác, logic trò chơi, camera và giao diện GUI."""

    def __init__(self, max_levels=33):
        """Khởi tạo bộ điều khiển trò chơi, thiết lập camera, giao diện HUD và tải màn đầu tiên."""
        self.max_levels = max_levels
        self.current_level_num = 1
        self.manual_moves = 0
        self.is_auto_playing = False
        self.current_replay_id = 0

        self.level = None
        self.game = None
        self.current_state = None
        self.board = None
        self.block = None
        self.cam_pivot = None
        self.target_fov = old_config.CAMERA_FOV

        self.hud = HUD(
            on_solve_click=self.solve_and_play,
            on_manual_click=self.switch_to_manual,
            on_level_change=self.change_level,
            on_select_level=self.select_stage_direct,
            on_restart_click=lambda: self.restart_with_fly_up(update_hud=True),
            max_levels=self.max_levels,
        )

        self.cam_pivot = Entity()
        camera.orthographic = old_config.CAMERA_ORTHOGRAPHIC
        camera.parent = self.cam_pivot
        camera.position = old_config.CAMERA_OFFSET
        camera.rotation = old_config.CAMERA_ROT
        camera.fov = old_config.CAMERA_FOV

        self.load_stage(self.current_level_num, initial=True)

    def is_tile_solid(self, r, c, bridges_mask):
        """Kiểm tra một ô tại vị trí (r, c) có phải là sàn vững chắc không (không phải Void hay Cầu đóng)."""
        if r < 0 or r >= self.level.rows or c < 0 or c >= self.level.cols:
            return False
        ch = self.level.grid[r][c]
        if ch in ("-", " "):
            return False
        bid = self.level.bridge_at.get((r, c))
        if bid is not None and bridges_mask is not None:
            idx = (
                self.level.bridge_order.index(bid)
                if bid in self.level.bridge_order
                else -1
            )
            if idx != -1 and not bridges_mask[idx]:
                return False
        return True

    def update(self):
        """Cập nhật vị trí camera bám theo khối gạch và xử lý xoay góc nhìn theo chuột mỗi khung hình."""
        if self.block:
            active_target = self.block.get_active_cube()
            if active_target:
                target_pos = Vec3(active_target.world_x, 0, active_target.world_z)
                self.cam_pivot.position = lerp(
                    self.cam_pivot.position,
                    target_pos,
                    time.dt * old_config.CAMERA_SPEED,
                )

            if held_keys["left mouse"]:
                self.cam_pivot.rotation_y += (
                    mouse.velocity[0] * old_config.MOUSE_SENSITIVITY
                )
                self.cam_pivot.rotation_x -= (
                    mouse.velocity[1] * old_config.MOUSE_SENSITIVITY
                )
            else:
                self.cam_pivot.rotation = lerp(
                    self.cam_pivot.rotation,
                    Vec3(0, 0, 0),
                    time.dt * old_config.RESET_SPEED,
                )

            camera.fov = lerp(
                camera.fov, self.target_fov, time.dt * old_config.ZOOM_SPEED
            )

    def handle_input(self, key):
        """Bắt và xử lý các sự kiện bàn phím cũng như thao tác cuộn chuột từ người dùng."""
        if key == "scroll up":
            self.target_fov = max(
                old_config.MIN_FOV, self.target_fov - old_config.ZOOM_STEP
            )
            return
        elif key == "scroll down":
            self.target_fov = min(
                old_config.MAX_FOV, self.target_fov + old_config.ZOOM_SPEED
            )
            return

        if self.is_auto_playing:
            return

        key_map = {
            "right arrow": Action.RIGHT,
            "left arrow": Action.LEFT,
            "up arrow": Action.UP,
            "down arrow": Action.DOWN,
            "space": Action.SWITCH,
        }
        if key in key_map:
            self.handle_action(key_map[key])
        elif key == "r":
            self.restart_with_fly_up(update_hud=True)

    def load_stage(self, level_num, initial=False):
        """Tải dữ liệu màn chơi mới và kích hoạt hiệu ứng chuyển cảnh tương ứng."""
        self.current_level_num = level_num
        self.is_auto_playing = False
        self.current_replay_id += 1
        self.manual_moves = 0

        def init_new_stage():
            if self.board:
                self.board.destroy_board()
            if self.block:
                self.block.destroy_block()

            path = Path(f"maps/level_{level_num:02d}.txt")
            if not path.exists():
                path = Path("maps/level_01.txt")

            self.level = load_level(path)
            self.game = BloxorzGame(self.level)
            self.current_state = self.game.start_state()

            start_r, start_c = self.level.start
            self.board = Board(self.level, animate_entrance=True, start_delay=0.3)
            self.board.sync_bridges(self.current_state.bridges, animate_entrance=True)
            self.block = Block(start_r, start_c)
            self.block.animate_drop_in(
                start_r, start_c, delay=self.board.get_entrance_duration()
            )

            self.cam_pivot.position = self.block.entity.world_position

            self.hud.update_level_display(level_num)
            self.hud.update_stats(f"[LEVEL {level_num:02d} - MANUAL MODE]\nMoves: 0")

        if not initial and self.board and self.block:
            self.block.animate_exit_fly_up(duration=0.4)
            self.board.animate_exit_fall_down(
                pause_duration=0.35, on_complete=init_new_stage
            )
        else:
            init_new_stage()

    def change_level(self, delta):
        """Chuyển đổi màn chơi theo bước tăng hoặc giảm chỉ định."""
        target = max(1, min(self.max_levels, self.current_level_num + delta))
        if target != self.current_level_num:
            self.load_stage(target)

    def select_stage_direct(self, level_num):
        """Tải trực tiếp màn chơi theo số màn được chọn."""
        if level_num != self.current_level_num:
            self.load_stage(level_num)

    def switch_to_manual(self):
        """Chuyển về chế độ người chơi tự điều khiển và làm mới lại bàn chơi."""
        if self.is_auto_playing:
            return
        self.restart_with_fly_up(update_hud=True)

    def reset_game(self, drop_in=False, on_complete=None, update_hud=True):
        """Đặt lại trạng thái màn chơi hiện tại về ban đầu."""
        self.is_auto_playing = False
        self.current_replay_id += 1

        self.manual_moves = 0
        if update_hud:
            self.hud.update_stats(
                f"[LEVEL {self.current_level_num:02d} - MANUAL MODE]\nMoves: {self.manual_moves}"
            )

        self.current_state = self.game.start_state()
        start_r, start_c = self.level.start

        self.board.sync_bridges(self.current_state.bridges)
        self.board.reset(animate_entrance=False)
        self.block.cleanup_split()

        if drop_in:
            self.block.animate_drop_in(
                start_r, start_c, delay=0.0, on_complete=on_complete
            )
        else:
            self.block.is_animating = False
            self.block.set_transform(start_r, start_c, "STANDING")

    def restart_with_fly_up(self, on_complete=None, update_hud=True):
        """Thực hiện hiệu ứng khối gạch bay vút lên và đặt lại màn chơi mượt mà."""
        self.is_auto_playing = False

        initial_bridges = self.game.start_state().bridges
        self.board.sync_bridges(initial_bridges)

        block_is_active = (
            self.block
            and hasattr(self.block, "entity")
            and self.block.entity
            and self.block.entity.enabled
            and not self.game.is_goal(self.current_state)
        )

        if block_is_active:

            def after_fly_up():
                self.reset_game(
                    drop_in=True, on_complete=on_complete, update_hud=update_hud
                )

            self.block.animate_exit_fly_up(duration=0.35, on_complete=after_fly_up)
        else:
            self.reset_game(
                drop_in=True, on_complete=on_complete, update_hud=update_hud
            )

    def solve_and_play(self, algo_name="astar"):
        """Khởi chạy luồng ngầm để tính toán lời giải AI và tự động phát lại các nước đi."""
        if self.is_auto_playing:
            return

        solver_fn = SOLVERS.get(algo_name)
        if not solver_fn:
            return

        self.hud.update_stats(f"[{algo_name.upper()}] Calculating solution...")

        def worker():
            solution = solver_fn(self.game)

            def on_solved():
                if not solution or not solution.solved:
                    self.hud.update_stats(f"[{algo_name.upper()}] No solution found!")
                    return

                def start_replay():
                    self.hud.update_stats(
                        f"[{algo_name.upper()} - LEVEL {self.current_level_num:02d}]\n"
                        f"Steps: {solution.solution_len} | Time: {solution.time_sec:.4f}s\n"
                        f"Expanded: {solution.expanded} | Peak Mem: {solution.peak_mem_bytes / 1024:.2f} KB"
                    )
                    self.is_auto_playing = True
                    self.execute_action_step(
                        solution.actions, 0, self.current_replay_id
                    )

                self.restart_with_fly_up(on_complete=start_replay, update_hud=False)

            invoke(on_solved)

        threading.Thread(target=worker, daemon=True).start()

    def execute_action_step(self, actions, index, replay_id):
        """Phát lại chuỗi nước đi do thuật toán giải lần lượt theo nhịp hoàn tất hoạt ảnh."""
        if not self.is_auto_playing or replay_id != self.current_replay_id:
            return

        if index >= len(actions):
            self.is_auto_playing = False
            return

        act = actions[index]

        def on_step_complete():
            if self.is_auto_playing and replay_id == self.current_replay_id:
                invoke(
                    lambda: self.execute_action_step(actions, index + 1, replay_id),
                    delay=0.08,
                )

        self.handle_action(act, on_complete=on_step_complete)

    def handle_action(self, action_enum: Action, on_complete=None):
        """Áp dụng nước đi của người chơi hoặc AI vào logic game và kích hoạt hoạt ảnh tương ứng."""
        if self.block.is_animating or self.game.is_goal(self.current_state):
            return

        next_state = self.game.apply(self.current_state, action_enum)

        if self.current_state.split:
            if action_enum == Action.SWITCH:
                if next_state is not None:
                    self.current_state = next_state
                    self.block.switch_active_cube()
                if on_complete:
                    invoke(on_complete, delay=0.1)
                return

            active_idx = self.current_state.active + 1
            cur_pos = self.current_state.active_pos()
            dr, dc = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}[
                action_enum.value
            ]
            next_r, next_c = cur_pos[0] + dr, cur_pos[1] + dc

            if next_state is not None:
                if not self.is_auto_playing:
                    self.manual_moves += 1
                    self.hud.update_stats(
                        f"[LEVEL {self.current_level_num:02d} - MANUAL MODE]\nMoves: {self.manual_moves}"
                    )

                def after_cube_move():
                    self.current_state = next_state
                    self.board.sync_bridges(self.current_state.bridges)

                    r1, c1 = next_state.a
                    r2, c2 = next_state.b
                    solid1 = self.is_tile_solid(r1, c1, next_state.bridges)
                    solid2 = self.is_tile_solid(r2, c2, next_state.bridges)

                    if not solid1 or not solid2:

                        def trigger_falls():
                            if not solid1:
                                self.block.animate_cube_fall(
                                    1, on_finish=lambda: self.reset_game(drop_in=True)
                                )
                            if not solid2:
                                self.block.animate_cube_fall(
                                    2, on_finish=lambda: self.reset_game(drop_in=True)
                                )

                        invoke(trigger_falls, delay=0.1)
                        return

                    if not next_state.split:
                        r1, c1 = next_state.a
                        r2, c2 = next_state.b
                        ori = next_state.orientation()
                        target_r = min(r1, r2) if ori == "LYING_V" else r1
                        target_c = min(c1, c2) if ori == "LYING_H" else c1

                        self.block.merge_cubes(
                            target_r, target_c, ori, on_complete=on_complete
                        )
                    else:
                        if on_complete:
                            on_complete()

                self.block.animate_cube_roll(
                    active_idx,
                    action_enum.value,
                    next_r,
                    next_c,
                    on_complete=after_cube_move,
                )
            else:

                def on_cube_fall():
                    self.block.animate_cube_fall(
                        active_idx, on_finish=lambda: self.reset_game(drop_in=True)
                    )

                self.block.animate_cube_roll(
                    active_idx,
                    action_enum.value,
                    next_r,
                    next_c,
                    on_complete=on_cube_fall,
                )

        else:
            if action_enum == Action.SWITCH:
                if on_complete:
                    on_complete()
                return

            cur_ori = self.current_state.orientation()
            if cur_ori == "STANDING":
                cur_r, cur_c = self.current_state.a
            elif cur_ori == "LYING_H":
                cur_r = self.current_state.a[0]
                cur_c = min(self.current_state.a[1], self.current_state.b[1])
            else:
                cur_r = min(self.current_state.a[0], self.current_state.b[0])
                cur_c = self.current_state.a[1]

            next_r, next_c, next_ori = self.get_next_transform(
                cur_r, cur_c, cur_ori, action_enum.value
            )
            pivot_pos, rot_axis = self.get_pivot_info(
                cur_r, cur_c, cur_ori, action_enum.value
            )

            if next_state is not None:
                if not self.is_auto_playing:
                    self.manual_moves += 1
                    self.hud.update_stats(
                        f"[LEVEL {self.current_level_num:02d} - MANUAL MODE]\nMoves: {self.manual_moves}"
                    )

                if next_state.split:

                    def after_roll_to_split():
                        self.current_state = next_state
                        self.board.sync_bridges(self.current_state.bridges)
                        self.block.split_into_cubes(next_state.a, next_state.b)
                        if on_complete:
                            on_complete()

                    self.block.animate_roll(
                        pivot_pos,
                        rot_axis,
                        next_r,
                        next_c,
                        next_ori,
                        on_complete=after_roll_to_split,
                    )
                else:

                    def after_roll():
                        self.current_state = next_state
                        self.board.sync_bridges(self.current_state.bridges)

                        if self.game.is_goal(self.current_state):

                            def on_win_finished():
                                self.is_auto_playing = False
                                self.hud.update_stats(
                                    self.hud.stats_text.text + "\nSTAGE CLEAR!"
                                )

                            self.block.animate_win(on_finish=on_win_finished)
                        else:
                            if on_complete:
                                on_complete()

                    self.block.animate_roll(
                        pivot_pos,
                        rot_axis,
                        next_r,
                        next_c,
                        next_ori,
                        on_complete=after_roll,
                    )

            else:

                def after_roll_fall():
                    if (
                        next_ori == "STANDING"
                        and (next_r, next_c) in self.level.fragile
                    ):
                        self.board.animate_break_tile(next_r, next_c)
                        invoke(
                            lambda: self.block.animate_fall(
                                level=self.level,
                                r=next_r,
                                c=next_c,
                                ori=next_ori,
                                bridges_mask=self.current_state.bridges,
                                on_finish=lambda: self.reset_game(drop_in=True),
                            ),
                            delay=0.15,
                        )
                    else:
                        self.block.animate_fall(
                            level=self.level,
                            r=next_r,
                            c=next_c,
                            ori=next_ori,
                            bridges_mask=self.current_state.bridges,
                            on_finish=lambda: self.reset_game(drop_in=True),
                        )

                self.block.animate_roll(
                    pivot_pos,
                    rot_axis,
                    next_r,
                    next_c,
                    next_ori,
                    on_complete=after_roll_fall,
                )

    @staticmethod
    def get_next_transform(r, c, ori, action):
        """Tính toán vị trí, hướng đặt tiếp theo của khối gạch sau khi thực hiện hành động."""
        if ori == "STANDING":
            mapping = {
                "RIGHT": (r, c + 1, "LYING_H"),
                "LEFT": (r, c - 2, "LYING_H"),
                "UP": (r - 2, c, "LYING_V"),
                "DOWN": (r + 1, c, "LYING_V"),
            }
        elif ori == "LYING_H":
            mapping = {
                "RIGHT": (r, c + 2, "STANDING"),
                "LEFT": (r, c - 1, "STANDING"),
                "UP": (r - 1, c, "LYING_H"),
                "DOWN": (r + 1, c, "LYING_H"),
            }
        elif ori == "LYING_V":
            mapping = {
                "RIGHT": (r, c + 1, "LYING_V"),
                "LEFT": (r, c - 1, "LYING_V"),
                "UP": (r - 1, c, "STANDING"),
                "DOWN": (r + 2, c, "STANDING"),
            }
        return mapping[action]

    @staticmethod
    def get_pivot_info(r, c, ori, action):
        """Tính toán tâm xoay (pivot) và trục xoay hình học cho khối gạch khi di chuyển."""
        if ori == "STANDING":
            mapping = {
                "RIGHT": ((c + 0.5, 0, -r), (0, 0, 90)),
                "LEFT": ((c - 0.5, 0, -r), (0, 0, -90)),
                "UP": ((c, 0, -r + 0.5), (90, 0, 0)),
                "DOWN": ((c, 0, -r - 0.5), (-90, 0, 0)),
            }
        elif ori == "LYING_H":
            mapping = {
                "RIGHT": ((c + 1.5, 0, -r), (0, 0, 90)),
                "LEFT": ((c - 0.5, 0, -r), (0, 0, -90)),
                "UP": ((c + 0.5, 0, -r + 0.5), (90, 0, 0)),
                "DOWN": ((c + 0.5, 0, -r - 0.5), (-90, 0, 0)),
            }
        elif ori == "LYING_V":
            mapping = {
                "RIGHT": ((c + 0.5, 0, -(r + 0.5)), (0, 0, 90)),
                "LEFT": ((c - 0.5, 0, -(r + 0.5)), (0, 0, -90)),
                "UP": ((c, 0, -r + 0.5), (90, 0, 0)),
                "DOWN": ((c, 0, -(r + 1.5)), (-90, 0, 0)),
            }
        return mapping[action]
