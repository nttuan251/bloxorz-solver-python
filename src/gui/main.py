from ursina import Ursina, camera
import config
from game_state import GameState
from board import Board
from block import Block

app = Ursina()

# 1. Khởi tạo dữ liệu & 3D Objects
matrix = [
    ['o', 'o', 'o'],
    ['o', 'S', 'o'],
    ['o', 'o', 'T']
]

state = GameState(matrix)
board = Board(matrix)
block = Block(state.cur_r, state.cur_c)

# 2. Setup Camera
camera.orthographic = config.CAMERA_ORTHOGRAPHIC
camera.position = config.CAMERA_POS
camera.rotation = config.CAMERA_ROT
camera.fov = config.CAMERA_FOV

# 3. Input Handling
def handle_action(action):
    if block.is_animating:
        return
    
    (next_r, next_c, next_ori), pivot_pos, rot_axis = state.get_next_state(action)
    state.cur_r, state.cur_c, state.cur_ori = next_r, next_c, next_ori
    
    block.animate_roll(pivot_pos, rot_axis, next_r, next_c, next_ori)

def input(key):
    key_map = {
        'right arrow': 'RIGHT',
        'left arrow': 'LEFT',
        'up arrow': 'UP',
        'down arrow': 'DOWN'
    }
    if key in key_map:
        handle_action(key_map[key])

app.run()