# main.py
from pathlib import Path
from ursina import Ursina, camera, Entity, Vec3, Button, Text, lerp, time, held_keys, mouse, invoke, destroy, color

from src.core.loader import load_level
from src.core.game import BloxorzGame
from src.core.tile import Action
from src.solvers import SOLVERS
from src.gui.board import Board
from src.gui.block import Block
import src.gui.config as config

app = Ursina()

# 1. Load Level từ file .txt
LEVEL_PATH = Path("maps/level07.txt")
level = load_level(LEVEL_PATH)
game = BloxorzGame(level)
current_state = game.start_state()

# 2. Khởi tạo Bàn chơi & Khối gạch
board = Board(level, animate_entrance=True, start_delay=0.6)
start_r, start_c = level.start
block = Block(start_r, start_c)

# 3. Setup Camera
cam_pivot = Entity(position=block.entity.world_position)
camera.orthographic = config.CAMERA_ORTHOGRAPHIC
camera.parent = cam_pivot
camera.position = config.CAMERA_OFFSET
camera.rotation = config.CAMERA_ROT
camera.fov = config.CAMERA_FOV
target_fov = config.CAMERA_FOV

# Intro Thả rơi gạch lần đầu mở màn
board_finish_time = board.get_entrance_duration()
block.animate_drop_in(start_r, start_c, delay=board_finish_time)

# Biến trạng thái Auto-Replay & Sequence ID
is_auto_playing = False
current_replay_id = 0

# 4. Bảng thông số HUD nằm gọn bên trái
stats_text = Text(
    text="[MANUAL MODE] Press arrow keys or select AI solver",
    position=(-0.85, 0.45),
    scale=1.0,
    color=color.yellow
)

def update():
    global target_fov
    if block:
        active_target = block.get_active_cube()
        if active_target:
            target_pos = Vec3(active_target.world_x, 0, active_target.world_z)
            cam_pivot.position = lerp(cam_pivot.position, target_pos, time.dt * config.CAMERA_SPEED)

        if held_keys['left mouse']:
            cam_pivot.rotation_y += mouse.velocity[0] * config.MOUSE_SENSITIVITY
            cam_pivot.rotation_x -= mouse.velocity[1] * config.MOUSE_SENSITIVITY
        else:
            cam_pivot.rotation = lerp(cam_pivot.rotation, Vec3(0, 0, 0), time.dt * config.RESET_SPEED)

        camera.fov = lerp(camera.fov, target_fov, time.dt * config.ZOOM_SPEED)

def reset_game(drop_in=False, on_complete=None):
    """Reset trạng thái game về ban đầu"""
    global current_state, is_auto_playing, current_replay_id
    is_auto_playing = False
    current_replay_id += 1  # Hủy các bước replay cũ đang chờ
    
    current_state = game.start_state()
    start_r, start_c = level.start

    board.sync_bridges(current_state.bridges)
    board.reset(animate_entrance=False)
    block.cleanup_split()
    
    if drop_in:
        block.animate_drop_in(
            start_r,
            start_c,
            delay=0.1,
            on_complete=on_complete
        )
    else:
        # Đặt gạch tĩnh tại chỗ không cần rơi từ trên cao
        block.is_animating = False
        block.set_transform(start_r, start_c, 'STANDING')

def switch_to_manual():
    """Chuyển về chế độ người chơi tự điều khiển"""
    if is_auto_playing:
        return

    reset_game(drop_in=True)
    stats_text.text = "[MANUAL MODE] Ready for arrow key inputs"


def solve_and_play(algo_name="astar"):
    global is_auto_playing, current_replay_id

    if is_auto_playing:
        return

    solver_fn = SOLVERS.get(algo_name)
    if not solver_fn:
        return

    # Tìm lời giải trước
    solution = solver_fn(game)

    if not solution.solved:
        reset_game(drop_in=True)
        stats_text.text = f"[{algo_name.upper()}] No solution found!"
        return

    stats_text.text = (
        f"[{algo_name.upper()}] Steps: {solution.solution_len} | "
        f"Time: {solution.time_sec:.4f}s | "
        f"Expanded: {solution.expanded}"
    )

    # Reset game và thả block xuống
    reset_game(drop_in=True)

    my_id = current_replay_id
    is_auto_playing = True

    # Chờ 1 giây cho animation thả block hoàn tất
    invoke(
        lambda: execute_action_step(solution.actions, 0, my_id),
        delay=1.0
    )


def execute_action_step(actions, index, replay_id):
    global is_auto_playing

    if not is_auto_playing or replay_id != current_replay_id:
        return

    if index >= len(actions):
        is_auto_playing = False
        stats_text.text += "\n🎉 STAGE CLEAR!"
        return

    act = actions[index]
    handle_action(act)

    step_delay = config.ROLL_DURATION + 0.08

    invoke(
        lambda: execute_action_step(actions, index + 1, replay_id),
        delay=step_delay
    )


def get_next_transform(r, c, ori, action):
    if ori == 'STANDING':
        mapping = {
            'RIGHT': (r, c + 1, 'LYING_H'),
            'LEFT':  (r, c - 2, 'LYING_H'),
            'UP':    (r - 2, c, 'LYING_V'),
            'DOWN':  (r + 1, c, 'LYING_V'),
        }
    elif ori == 'LYING_H':
        mapping = {
            'RIGHT': (r, c + 2, 'STANDING'),
            'LEFT':  (r, c - 1, 'STANDING'),
            'UP':    (r - 1, c, 'LYING_H'),
            'DOWN':  (r + 1, c, 'LYING_H'),
        }
    elif ori == 'LYING_V':
        mapping = {
            'RIGHT': (r, c + 1, 'LYING_V'),
            'LEFT':  (r, c - 1, 'LYING_V'),
            'UP':    (r - 1, c, 'STANDING'),
            'DOWN':  (r + 2, c, 'STANDING'),
        }
    return mapping[action]

def get_pivot_info(r, c, ori, action):
    if ori == 'STANDING':
        mapping = {
            'RIGHT': ((c + 0.5, 0, -r), (0, 0, 90)),
            'LEFT':  ((c - 0.5, 0, -r), (0, 0, -90)),
            'UP':    ((c, 0, -r + 0.5), (90, 0, 0)),
            'DOWN':  ((c, 0, -r - 0.5), (-90, 0, 0)),
        }
    elif ori == 'LYING_H':
        mapping = {
            'RIGHT': ((c + 1.5, 0, -r), (0, 0, 90)),
            'LEFT':  ((c - 0.5, 0, -r), (0, 0, -90)),
            'UP':    ((c + 0.5, 0, -r + 0.5), (90, 0, 0)),
            'DOWN':  ((c + 0.5, 0, -r - 0.5), (-90, 0, 0)),
        }
    elif ori == 'LYING_V':
        mapping = {
            'RIGHT': ((c + 0.5, 0, -(r + 0.5)), (0, 0, 90)),
            'LEFT':  ((c - 0.5, 0, -(r + 0.5)), (0, 0, -90)),
            'UP':    ((c, 0, -r + 0.5), (90, 0, 0)),
            'DOWN':  ((c, 0, -(r + 1.5)), (-90, 0, 0)),
        }
    return mapping[action]

def handle_action(action_enum: Action):
    global current_state
    if block.is_animating:
        return

    next_state = game.apply(current_state, action_enum)

    if current_state.split:
        if action_enum == Action.SWITCH:
            if next_state is not None:
                current_state = next_state
                block.switch_active_cube()
            return

        active_idx = current_state.active + 1
        cur_pos = current_state.active_pos()
        dr, dc = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}[action_enum.value]
        next_r, next_c = cur_pos[0] + dr, cur_pos[1] + dc

        if next_state is not None:
            def after_cube_move():
                global current_state
                current_state = next_state
                board.sync_bridges(current_state.bridges)

                if not next_state.split:
                    r1, c1 = next_state.a
                    r2, c2 = next_state.b
                    ori = next_state.orientation()
                    target_r = min(r1, r2) if ori == 'LYING_V' else r1
                    target_c = min(c1, c2) if ori == 'LYING_H' else c1
                    block.merge_cubes(target_r, target_c, ori)

            block.animate_cube_roll(active_idx, action_enum.value, next_r, next_c, on_complete=after_cube_move)
        else:
            block.animate_cube_roll(
                active_idx, action_enum.value, next_r, next_c,
                on_complete=lambda: block.animate_cube_fall(active_idx, on_finish=lambda: reset_game(drop_in=True))
            )

    else:
        if action_enum == Action.SWITCH:
            return

        cur_ori = current_state.orientation()
        if cur_ori == 'STANDING':
            cur_r, cur_c = current_state.a
        elif cur_ori == 'LYING_H':
            cur_r = current_state.a[0]
            cur_c = min(current_state.a[1], current_state.b[1])
        else:
            cur_r = min(current_state.a[0], current_state.b[0])
            cur_c = current_state.a[1]

        next_r, next_c, next_ori = get_next_transform(cur_r, cur_c, cur_ori, action_enum.value)
        pivot_pos, rot_axis = get_pivot_info(cur_r, cur_c, cur_ori, action_enum.value)

        if next_state is not None:
            if next_state.split:
                def after_roll_to_split():
                    global current_state
                    current_state = next_state
                    board.sync_bridges(current_state.bridges)
                    block.split_into_cubes(next_state.a, next_state.b)

                block.animate_roll(pivot_pos, rot_axis, next_r, next_c, next_ori, on_complete=after_roll_to_split)
            else:
                def after_roll():
                    global current_state
                    current_state = next_state
                    board.sync_bridges(current_state.bridges)
                    if game.is_goal(current_state):
                        block.animate_win(on_finish=lambda: print("🎉 STAGE CLEAR! 🎉"))

                block.animate_roll(pivot_pos, rot_axis, next_r, next_c, next_ori, on_complete=after_roll)

        else:
            def after_roll_fall():
                if next_ori == 'STANDING' and (next_r, next_c) in level.fragile:
                    board.animate_break_tile(next_r, next_c)
                    invoke(lambda: block.animate_fall(
                        level=level, r=next_r, c=next_c, ori=next_ori,
                        bridges_mask=current_state.bridges, on_finish=lambda: reset_game(drop_in=True)
                    ), delay=0.15)
                else:
                    block.animate_fall(
                        level=level, r=next_r, c=next_c, ori=next_ori,
                        bridges_mask=current_state.bridges, on_finish=lambda: reset_game(drop_in=True)
                    )

            block.animate_roll(pivot_pos, rot_axis, next_r, next_c, next_ori, on_complete=after_roll_fall)

# 5. DÀN NÚT BẤM CĂN PHẢI (KHÔNG CHE CHỮ HUD)
btn_bfs = Button(text='BFS', color=color.azure, scale=(0.10, 0.05), position=(0.15, 0.43), on_click=lambda: solve_and_play('bfs'))
btn_dfs = Button(text='DFS', color=color.orange, scale=(0.10, 0.05), position=(0.26, 0.43), on_click=lambda: solve_and_play('dfs'))
btn_ucs = Button(text='UCS', color=color.cyan, scale=(0.10, 0.05), position=(0.37, 0.43), on_click=lambda: solve_and_play('ucs'))
btn_astar = Button(text='A*', color=color.lime, scale=(0.10, 0.05), position=(0.48, 0.43), on_click=lambda: solve_and_play('astar'))
btn_manual = Button(text='MANUAL', color=color.red, scale=(0.12, 0.05), position=(0.60, 0.43), on_click=switch_to_manual)

def input(key):
    global target_fov
    if is_auto_playing:
        return

    key_map = {
        'right arrow': Action.RIGHT,
        'left arrow': Action.LEFT,
        'up arrow': Action.UP,
        'down arrow': Action.DOWN,
        'space': Action.SWITCH
    }
    if key in key_map:
        handle_action(key_map[key])
    elif key == 'r':
        reset_game(drop_in=True)
    elif key == 'scroll up':
        target_fov = max(config.MIN_FOV, target_fov - config.ZOOM_STEP)
    elif key == 'scroll down':
        target_fov = min(config.MAX_FOV, target_fov + config.ZOOM_SPEED)

app.run()