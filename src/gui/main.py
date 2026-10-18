"""Ursina 3D GUI wired to src/core + src/solvers.

Manual: arrows/WASD roll, Space switch cube, R restart, N/P prev/next level.
Solvers: BFS / DFS / UCS / A* buttons solve in a worker thread then replay.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ursina import (Button, Slider, Text, Ursina, Vec3, camera, destroy)

import config as config
from block import Block
from board import Board
from controller import GameController
from core.tile import Action
from solvers import solve_astar, solve_bfs, solve_dfs, solve_ucs

SOLVER_FNS = {"BFS": solve_bfs, "DFS": solve_dfs, "UCS": solve_ucs, "A*": solve_astar}
KEYMAP = {
    'up arrow': Action.UP, 'w': Action.UP,
    'down arrow': Action.DOWN, 's': Action.DOWN,
    'left arrow': Action.LEFT, 'a': Action.LEFT,
    'right arrow': Action.RIGHT, 'd': Action.RIGHT,
}

app = Ursina()
# Hide built-in debug widgets so they never cover our buttons (top-right).
try:
    from ursina import window as _window
    for _attr in ('fps_counter', 'entity_counter', 'collider_counter'):
        try:
            getattr(_window, _attr).enabled = False
        except Exception:
            pass
    try:
        _window.exit_button.visible = False
    except Exception:
        pass
    _window.title = 'Bloxorz 3D'
except Exception:
    pass


def list_levels():
    root = Path(__file__).resolve().parents[2] / 'maps'
    files = sorted([p for p in root.glob('level*.txt')
                    if p.name != 'MAP_FORMAT.txt' and not p.name.startswith('_')])
    if not files:
        files = sorted(root.glob('*.txt'))
    return files


class Gui:
    def __init__(self):
        self.level_files = list_levels()
        self.level_idx = 0
        self.controller: GameController | None = None
        self.board: Board | None = None
        self.block: Block | None = None
        self.replay: list[Action] = []
        self.replay_i = 0
        self.replaying = False
        self.replay_acc = 0.0
        self.speed = config.REPLAY_DEFAULT_SPEED
        self.solving = False
        self.cam_offset = config.follow_offset()
        self._build_ui()
        self.load_level(0)

    # ---------- UI ----------
    # Safe zone: keep everything inside x in [-0.72, 0.72], y <= 0.38 so the
    # top-right corner (Ursina window chrome) is never covered.
    def _build_ui(self):
        self.title = Text(text=' ', origin=(0, 0), position=(-0.46, 0.45),
                          scale=1.0)
        self.status = Text(text=' ', origin=(0, 0), position=(-0.46, 0.40),
                           scale=0.85)
        self.stats = Text(text=' ', origin=(0, 0), position=(-0.46, 0.33),
                          scale=0.8)
        self.msg = Text(text=' ', origin=(0, 0), position=(0, 0.12),
                        scale=2.2)
        self.help = Text(
            text='Arrows/WASD move | Space switch cube | R restart | N/P level',
            origin=(0, 0), position=(0, -0.46), scale=0.75)

        self.btn_prev = Button(text='Prev', position=(0.47, 0.36),
                               scale=(0.11, 0.055), on_click=self.prev_level)
        self.btn_next = Button(text='Next', position=(0.63, 0.36),
                               scale=(0.11, 0.055), on_click=self.next_level)
        self.btn_restart = Button(text='Restart (R)', position=(0.55, 0.28),
                                  scale=(0.27, 0.055), on_click=self.restart)
        self.solver_btns = {}
        _xs = (0.47, 0.63)
        _ys = (0.20, 0.13)
        for i, name in enumerate(["BFS", "DFS", "UCS", "A*"]):
            b = Button(text=f'Solve {name}',
                       position=(_xs[i % 2], _ys[i // 2]),
                       scale=(0.125, 0.055),
                       on_click=self._make_solver_cb(name))
            self.solver_btns[name] = b
        self.btn_stop = Button(text='Stop replay', position=(0.55, 0.02),
                               scale=(0.27, 0.055), on_click=self.stop_replay)
        try:
            self.slider = Slider(min=1, max=10, default=self.speed,
                                 text='Speed', position=(0.55, -0.06),
                                 scale=(0.27, 0.05))
        except Exception:
            self.slider = None

    def _make_solver_cb(self, name):
        return lambda: self.solve(name)

    # ---------- level mgmt ----------
    def load_level(self, idx: int):
        self.stop_replay()
        self.level_idx = idx % len(self.level_files)
        path = self.level_files[self.level_idx]
        if self.board:
            self.board.destroy()
        if self.block:
            self.block.destroy()
        self.controller = GameController.from_file(path)
        self.board = Board(self.controller.level)
        self.block = Block()
        self.block.sync(self.controller.state)
        self.board.refresh(self.controller.state)
        self._fit_camera()
        self.msg.text = ' '
        self.stats.text = ' '
        self._refresh_labels()
        self._refresh_status('playing')

    def _fit_camera(self):
        camera.orthographic = config.CAMERA_ORTHOGRAPHIC
        camera.rotation = config.CAMERA_ROT
        camera.fov = config.FOLLOW_FOV
        self._snap_camera()

    def _focus_point(self):
        """World point the camera follows: active cube, else block center."""
        try:
            if self.block is not None:
                if self.block._split:
                    st = self.controller.state if self.controller else None
                    active = st.active if st is not None else 0
                    e = self.block.cube_a if active == 0 else self.block.cube_b
                    return Vec3(e.x, 0, e.z)
                return Vec3(self.block.main.x, 0, self.block.main.z)
        except Exception:
            pass
        # Fallback: board midpoint.
        try:
            lv = self.controller.level
            return Vec3((lv.cols - 1) / 2.0, 0, -((lv.rows - 1) / 2.0))
        except Exception:
            return Vec3(0, 0, 0)

    def _snap_camera(self):
        camera.position = self._focus_point() + self.cam_offset

    def _update_camera(self, dt: float):
        try:
            desired = self._focus_point() + self.cam_offset
            k = min(1.0, dt * 10.0)
            camera.position = camera.position + (desired - camera.position) * k
        except Exception:
            pass

    def prev_level(self):
        self.load_level(self.level_idx - 1)

    def next_level(self):
        self.load_level(self.level_idx + 1)

    def restart(self):
        if not self.controller:
            return
        self.stop_replay()
        self.block.sync(self.controller.restart())
        self.board.refresh(self.controller.state)
        self._snap_camera()
        self.msg.text = ' '
        self.stats.text = ' '
        self._refresh_status('playing')

    # ---------- labels ----------
    def _refresh_labels(self):
        p = self.level_files[self.level_idx]
        lv = self.controller.level
        self.title.text = f'{p.name}  [{self.level_idx + 1}/{len(self.level_files)}]  {lv.rows}x{lv.cols}'

    def _refresh_status(self, event: str):
        s = self.controller.state
        if self.controller.status == 'won':
            self.status.text = 'Status: WON! Press R or N.'
            self.msg.text = 'YOU WIN!'
        elif self.controller.status == 'lost':
            self.status.text = 'Status: FELL. Press R to retry.'
            self.msg.text = 'FELL!'
        else:
            ori = s.orientation() if s else '?'
            extra = f' active={s.active_pos()}' if s and s.split else ''
            self.status.text = f'Status: {ori}{extra}  bridges={list(s.bridges) if s else []}'

    # ---------- manual play ----------
    def manual(self, action: Action):
        if self.solving or self.replaying or not self.controller:
            return
        if self.block.is_animating or self.controller.status != 'playing':
            return
        old = self.controller.state
        nxt, event = self.controller.do_action(action)
        if event == 'ignored':
            return
        if nxt is None:  # fell: roll out to the void cells, then drop
            preview = self.controller.game.preview_cells(old, action)
            self.block.animate_roll_then_fall(
                old, action, preview,
                done=lambda: self._refresh_status('fell'))
            self._refresh_status('fell')
            return
        self.block.animate_to(old, action, nxt,
                              done=lambda: (self.board.refresh(nxt),
                                            self._refresh_status(event)))

    # ---------- solvers ----------
    def solve(self, name: str):
        if self.solving or self.replaying or not self.controller:
            return
        if self.controller.status != 'playing':
            self.restart()
        self.solving = True
        self.msg.text = f'Solving {name} ...'
        self.stats.text = ' '
        game, start = self.controller.game, self.controller.state
        self.solve_start = start
        fn = SOLVER_FNS[name]

        def _work():
            sol = fn(game, start)
            # Back to main thread for Ursina entities.
            from ursina import invoke as _invoke
            _invoke(lambda: self._on_solved(name, sol), delay=0)

        threading.Thread(target=_work, daemon=True).start()

    def _on_solved(self, name, sol):
        self.solving = False
        if not sol.solved:
            self.msg.text = f'{name}: NO SOLUTION (expanded {sol.expanded})'
            self.stats.text = (f'{name} expanded={sol.expanded} '
                               f'time={sol.time_sec:.3f}s mem={sol.peak_mem_bytes // 1024}KB')
            return
        self.msg.text = ' '
        self.stats.text = (f'{name}: len={sol.solution_len} expanded={sol.expanded} '
                           f'time={sol.time_sec:.3f}s mem={sol.peak_mem_bytes // 1024}KB')
        # Replay from the exact state the solver started at.
        self.stop_replay()
        self.controller.reset_to(getattr(self, 'solve_start', self.controller.start))
        self.block.sync(self.controller.state)
        self.board.refresh(self.controller.state)
        self._snap_camera()
        self._refresh_status('playing')
        self.replay = list(sol.actions)
        self.replay_i = 0
        self.replay_acc = 0.0
        self.replaying = True

    def stop_replay(self):
        self.replaying = False
        self.replay = []
        self.replay_i = 0

    # ---------- replay tick ----------
    def tick(self, dt: float):
        if self.slider is not None:
            try:
                self.speed = float(self.slider.value)
            except Exception:
                pass
        # Follow cam runs every frame (manual, replay, idle).
        if self.controller is not None and self.block is not None:
            self._update_camera(dt)
        if not self.replaying or not self.controller:
            return
        if self.block.is_animating or self.controller.status != 'playing':
            if self.controller.status in ('won', 'lost'):
                self.replaying = False
                self._refresh_status(self.controller.status)
            return
        self.replay_acc += dt
        interval = 1.0 / max(0.5, self.speed)
        # Wait until enough time passed AND roll animation slot is free.
        if self.replay_acc < interval:
            return
        if self.replay_i >= len(self.replay):
            self.replaying = False
            return
        self.replay_acc = 0.0
        action = self.replay[self.replay_i]
        self.replay_i += 1
        old = self.controller.state
        nxt, event = self.controller.do_action(action)
        if nxt is None:
            preview = self.controller.game.preview_cells(old, action)
            self.block.animate_roll_then_fall(
                old, action, preview,
                done=lambda: self._refresh_status('fell'))
            self.replaying = False
            return

        def _done(n=nxt, e=event):
            self.board.refresh(n)
            self._refresh_status(e)
            if self.controller.status != 'playing':
                self.replaying = False

        self.block.animate_to(old, action, nxt, done=_done)


gui = Gui()


def input(key):  # noqa: A001 - Ursina hook
    if key in KEYMAP:
        gui.manual(KEYMAP[key])
    elif key == 'space':
        gui.manual(Action.SWITCH)
    elif key in ('r', 'R'):
        gui.restart()
    elif key in ('n', 'N'):
        gui.next_level()
    elif key in ('p', 'P'):
        gui.prev_level()


def update():
    import time
    dt = min(0.1, time.dt if hasattr(time, 'dt') else 1 / 60)
    # Ursina provides time.dt; fall back above.
    try:
        from ursina import time as utime
        dt = min(0.1, utime.dt)
    except Exception:
        pass
    gui.tick(dt)


app.run()
