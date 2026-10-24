# Bloxorz Solver

## Web GUI (three.js)

The game and the solvers are Python. The web GUI only draws: every move and every search
runs in `src/` through a small local server.

```
python -m web.server
```

This starts the server at http://127.0.0.1:8000 and opens it in your browser. It needs only the
Python standard library: no `pip install`, no Ursina or Panda3D. Use `--port 9000` to change
the port, `--no-browser` to skip opening a tab.

Controls: arrow keys (or WASD) roll the block, Space switches cubes after a split, R restarts,
N picks a level, H shows help, C resets the camera, T switches between the two colour themes
(Aurora with a black hole, Dusk with the sun and clouds). Drag to orbit, scroll to zoom.
Clearing a level sets off fireworks over the goal and loads the next level.

The solver panel runs BFS, DFS, UCS or A* on the current level, replays the answer and
shows steps, path cost, expanded nodes, time and peak memory. "Show explored tiles" colours
every tile by how many expanded states touched it. "Compare all" runs the four solvers
side by side.

### How it fits together

```
browser (web/static)                 Python (web/server.py -> web/api.py -> src/)
three.js scene, HUD, animation  <->  GET  /api/levels, /api/levels/<id>, /api/options
                                     POST /api/step   {level, state, action}
                                     POST /api/solve  {level, solver, cost, heuristic}
```

- `web/api.py` turns engine states into JSON and back. UCS is A* with the `TRIVIAL` heuristic.
- `web/static/js/` holds the front end: `scene.js` (renderer, camera), `board.js` (tiles,
  bridges, switches, heat map), `block.js` (block and cube animations), `main.js` (game flow).
- three.js r160 is vendored in `web/static/vendor/`, so the game runs offline. Fonts load
  from Google Fonts and fall back to system fonts without internet.

Tests: `python -m unittest discover tests`

## Desktop GUI (Ursina)

`python main.py` still starts the original Ursina GUI.
