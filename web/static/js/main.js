// Game controller: wires keyboard and HUD to the Python engine and drives the 3D scene.
import * as THREE from "three";
import { api } from "./api.js";
import { Stage } from "./scene.js";
import { Board, plankTint } from "./board.js";
import { Block } from "./block.js";
import { finishAll, setSpeed, wait } from "./tween.js";
import { THEMES, themeById } from "./themes.js";
import { fireworks } from "./fireworks.js";
import { crackTexture, plankTexture } from "./geometry.js";

const $ = id => document.getElementById(id);
const ACTIONS = { UP: [0, -1], DOWN: [0, 1], LEFT: [-1, 0], RIGHT: [1, 0] };

const ALGO_NOTES = {
  BFS: "Breadth-first: explores level by level, so it finds the fewest moves.",
  DFS: "Depth-first: dives down one branch at a time. Fast to finish, but the path is usually long.",
  UCS: "Uniform-cost: always expands the cheapest path so far. Uses the step cost below.",
  "A*": "A*: cheapest path so far plus a heuristic estimate of what is left.",
};

/** The bridge texture multiplied by the theme's plank tint, exactly as Board colours it. */
function tintedPlanks(wood) {
  const src = plankTexture.image;
  const c = document.createElement("canvas");
  c.width = src.width;
  c.height = src.height;
  const g = c.getContext("2d");
  g.drawImage(src, 0, 0);
  g.globalCompositeOperation = "multiply";
  g.fillStyle = `#${plankTint(new THREE.Color(wood)).getHexString()}`;
  g.fillRect(0, 0, c.width, c.height);
  return c.toDataURL();
}

const store = {
  get(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ } },
};

class Game {
  constructor() {
    this.stage = new Stage($("scene"));
    this.theme = themeById(store.get("theme", THEMES[0].id));
    this._applyThemeCss(this.theme);
    this.stage.applyTheme(this.theme);
    this.levels = [];
    this.level = null;
    this.board = null;
    this.block = null;
    this.state = null;
    this.moves = 0;
    this.busy = false;
    this.queued = null;
    this.playing = null; // { result, index, paused }
    this.result = null;
    this.compareRows = [];
    this.par = new Map();
    this.solver = store.get("solver", "A*");
    this.loadToken = 0;
    this.done = new Set(store.get("done", []));
  }

  async boot() {
    try {
      const [levels, options] = await Promise.all([api.levels(), api.options()]);
      if (!levels.length) throw new Error("No level files were found in the maps folder.");
      this.levels = levels;
      this.options = options;
    } catch (err) {
      const boot = $("boot");
      boot.classList.add("error");
      $("boot-text").textContent = `Could not reach the game server. Start it from the project folder with "python -m web.server", then reload. (${err.message})`;
      return;
    }
    this._buildHud();
    this._buildThemes();
    this._bindKeys();
    const saved = store.get("level", this.levels[0].id);
    await this.load(this.levels.some(l => l.id === saved) ? saved : this.levels[0].id);
    $("boot").classList.add("gone");
  }

  // ---------- levels ----------

  async load(id, { animateOut = true } = {}) {
    this.stopPlayback();
    this.busy = true;
    // a newer load (or restart) may start while this one waits; the older one then just stops
    const token = ++this.loadToken;
    this.queued = null; // keys pressed for the old level must not move the new one
    const data = await api.level(id);
    if (token !== this.loadToken) return;
    if (this.board && animateOut) await Promise.all([this.board.exit(), this.block?.exit()]);
    if (token !== this.loadToken) return;
    finishAll();
    this.block?.dispose();
    this.board?.dispose();

    this.level = data;
    this.won = false;
    this.levelIndex = this.levels.findIndex(l => l.id === id);
    store.set("level", id);
    $("level-number").textContent = this.levels[this.levelIndex].number;
    this._setResult(null);
    this.compareRows = [];
    $("compare").hidden = true;

    this.stage.frame(data.rows, data.cols);
    this.board = new Board(this.stage, data);
    await this.board.setBridges(data.state.bridges, false);
    this.block = new Block(this.stage, this.board);
    this.block.set(data.state);
    this.block.whole.visible = false;
    this.state = data.state;
    this._setMoves(0);
    this._showPar();

    await this.board.enter();
    if (token !== this.loadToken) return;
    await this.block.dropIn(data.state);
    if (token !== this.loadToken) return;
    this.queued = null;
    this.busy = false;
  }

  async restart({ quiet = false } = {}) {
    if (!this.board) return;
    this.stopPlayback();
    this.won = false;
    const token = ++this.loadToken;
    this.busy = true;
    this.queued = null; // keys mashed while the block was falling are dropped, not replayed later
    finishAll();
    this.board.clearSearch();
    this.board.restoreTiles();
    this.board.bridgeOpen.clear();
    await this.board.setBridges(this.level.state.bridges, false);
    this.state = this.level.state;
    this._setMoves(0);
    this.busy = true;
    await this.block.dropIn(this.state);
    if (token !== this.loadToken) return;
    this.queued = null;
    this.busy = false;
    if (!quiet) this._toast("Level restarted");
  }

  // ---------- themes ----------

  async setTheme(id) {
    const theme = themeById(id);
    this.theme = theme;
    store.set("theme", theme.id);
    this._applyThemeCss(theme);
    this.stage.applyTheme(theme);
    this._syncThemes();
    if (!this.level) return;
    // rebuild the board and block in the new colours, keeping the current position
    this.stopPlayback();
    while (this.busy) await this._delay(30);
    if (this.theme !== theme) return; // a newer pick arrived while waiting
    this.busy = true;
    finishAll();
    this.block.dispose();
    this.board.dispose();
    this.board = new Board(this.stage, this.level);
    this.board.setBridges(this.state.bridges, false); // no animation: applied synchronously
    this.block = new Block(this.stage, this.board);
    this.block.set(this.state);
    if (this.won) this.block.whole.visible = false; // already sank into the goal
    if (this.result) this._applySearchLayer(this.result);
    this.busy = false;
  }

  /** themes.js is the one source of colours: copy the board colours into CSS for the legends. */
  _applyThemeCss(theme) {
    const root = document.documentElement;
    root.dataset.theme = theme.id;
    const b = theme.board;
    const vars = {
      "--heat-low": b.heatLow, "--heat-mid": b.heatMid, "--heat-high": b.heatHigh,
      "--tile-floor": b.stone, "--tile-fragile": b.fragile, "--tile-wood": b.wood,
      "--tile-brass": b.brass, "--tile-hole": b.hole, "--tile-glow": b.glow,
    };
    for (const [k, v] of Object.entries(vars)) root.style.setProperty(k, v);
    // the legend draws the very same canvas textures the tiles use
    root.style.setProperty("--tex-crack", `url(${crackTexture.image.toDataURL()})`);
    root.style.setProperty("--tex-plank", `url(${tintedPlanks(b.wood)})`);
  }

  _syncThemes() {
    $("theme-name").textContent = this.theme.name;
    for (const b of $("themes").querySelectorAll("button")) b.setAttribute("aria-checked", String(b.dataset.theme === this.theme.id));
  }

  // ---------- moving ----------

  /** Map an arrow key to the engine action that looks like that direction on screen. */
  screenToAction(key) {
    const f = this.stage.forward();
    const right = { x: -f.y, y: f.x };
    const want = { up: [f.x, f.y], down: [-f.x, -f.y], right: [right.x, right.y], left: [-right.x, -right.y] }[key];
    let best = "UP", bestDot = -Infinity;
    for (const [action, [dx, dz]] of Object.entries(ACTIONS)) {
      const dot = dx * want[0] + dz * want[1];
      if (dot > bestDot) { bestDot = dot; best = action; }
    }
    return best;
  }

  request(action) {
    if (this.playing) this.stopPlayback();
    if (this.won && !this.busy) { this.restart({ quiet: true }); return; } // block is in the goal: start over
    if (this.busy) { this.queued = action; return; }
    this.move(action);
  }

  _flushQueue() {
    if (this.queued && !this.busy) {
      const a = this.queued;
      this.queued = null;
      this.move(a);
    }
  }

  async move(action) {
    if (!this.state) return;
    if (action === "SWITCH_CONTROL" && !this.state.split) return;
    this.busy = true;
    const token = this.loadToken; // a level load or restart started meanwhile makes this move stale
    try {
      const prev = this.state;
      const res = await api.step(this.level.id, prev, action);
      if (token !== this.loadToken) return;
      if (!res.ok) {
        await this._fail(prev, action, res, token);
        return;
      }
      if (!(await this._applyMove(prev, action, res, token))) return;
      if (res.won) await this._win();
    } catch (err) {
      this._toast(err.message, true);
    } finally {
      if (token === this.loadToken) {
        this.busy = false;
        this._flushQueue();
      }
    }
  }

  /** Animate one legal move and commit it. Returns false if a load or restart cut it short. */
  async _applyMove(prev, action, res, token) {
    if (action !== "SWITCH_CONTROL") await this.block.roll(prev, action);
    if (token !== this.loadToken) return false;
    const next = res.state;
    const moved = res.moved;

    // switches: press whatever the block now covers if anything changed
    const bridgeChanged = JSON.stringify(prev.bridges) !== JSON.stringify(next.bridges);
    const splitChanged = prev.split !== next.split && next.split;
    if (bridgeChanged || splitChanged) {
      for (const [r, c] of [moved.a, moved.b]) if (this.board.isSwitch(r, c)) this.board.press(r, c);
    }
    const changed = await Promise.all([
      this.board.setBridges(next.bridges, true),
      this.block.settle(prev, moved, next),
    ]).then(([c]) => c);
    if (token !== this.loadToken) return false;

    if (splitChanged) this._toast("The block split. Press Space to switch cubes.");
    else if (prev.split && !next.split) this._toast("Cubes joined back together");
    else if (changed.length) {
      const opened = changed.filter(b => b.open).length;
      const closed = changed.length - opened;
      this._toast(opened && closed ? "Bridges changed" : opened ? "Bridge opened" : "Bridge closed");
    }
    this.state = next;
    // switching cubes is not a move (project FAQ #23); only rolls are counted
    if (action !== "SWITCH_CONTROL") this._setMoves(this.moves + 1);
    return true;
  }

  async _fail(prev, action, res, token) {
    const moved = res.moved;
    if (res.reason === "fragile") {
      this._toast("The fragile tile cracked under the block", true);
      await Promise.all([this.block.fall(prev, action, res.reason), this._delay(260).then(() => this.board.shatter(...moved.a))]);
    } else if (res.reason === "blocked") {
      await this.block.nudge(action);
      return;
    } else {
      this._toast("Fell off the edge", true);
      await this.block.fall(prev, action, res.reason);
    }
    await this._delay(250);
    if (token === this.loadToken) await this.restart({ quiet: true });
  }

  /**
   * Level cleared: the block sinks, fireworks go up over the goal. After a manual win the
   * next level loads by itself; after a solver replay the level stays so the metrics and
   * explored tiles can still be read.
   */
  async _win({ advance = true } = {}) {
    this.stopPlayback();
    this.won = true;
    this.done.add(this.level.id);
    store.set("done", [...this.done]);
    const level = this.level;
    const token = this.loadToken;
    this.busy = true;
    const goal = this.board.world(...level.goal);
    await this.block.sink();
    const show = fireworks(this.stage, goal, this.theme.glow);
    await this._delay(2600);
    if (token !== this.loadToken) return; // the player already picked another level or restarted
    this.busy = false;
    if (advance && this.level === level) {
      const next = this.levels[(this.levelIndex + 1) % this.levels.length];
      await this.load(next.id);
    }
    await show;
  }

  _delay(ms) { return wait(ms, false); }

  // ---------- solving ----------

  _solverArgs(name = this.solver) {
    return [this.level.id, name, $("sel-cost").value, $("sel-heuristic").value];
  }

  async solve() {
    const btn = $("btn-solve");
    btn.disabled = true;
    btn.textContent = "Searching…";
    try {
      const args = this._solverArgs();
      const result = await api.solve(...args);
      if (args[0] !== this.level.id) return; // the player switched levels while it was searching
      this._rememberPar(result);
      this._setResult(result);
      this.play(result);
    } catch (err) {
      this._toast(err.message, true);
    } finally {
      btn.disabled = false;
      btn.textContent = "Solve and play";
    }
  }

  async compare() {
    const btn = $("btn-compare");
    btn.disabled = true;
    const rows = [];
    try {
      for (const s of this.options.solvers) {
        btn.textContent = `Running ${s.name}…`;
        const args = this._solverArgs(s.name);
        rows.push(await api.solve(...args));
        if (args[0] !== this.level.id) return;
      }
      rows.forEach(r => this._rememberPar(r));
      this.compareRows = rows;
      this._renderCompare();
      $("compare").hidden = false;
    } catch (err) {
      this._toast(err.message, true);
    } finally {
      btn.disabled = false;
      btn.textContent = "Compare all";
    }
  }

  _rememberPar(result) {
    if (result.found && (result.solver === "BFS")) {
      this.par.set(this.level.id, result.metrics.steps);
      this._showPar();
    }
  }

  async play(result) {
    this.stopPlayback();
    if (!result.found) {
      this._toast("No solution exists from the start of this level", true);
      return;
    }
    // solvers search from the start state, so the replay starts there too
    while (this.busy) await this._delay(30);
    if (result.level !== this.level.id) return; // a solution for a level we already left
    if (this.moves > 0 || JSON.stringify(this.state) !== JSON.stringify(this.level.state)) await this.restart({ quiet: true });
    this._applySearchLayer(result);
    const token = this.loadToken;

    const run = { result, index: 0, paused: false, stopped: false };
    this.playing = run;
    setSpeed(this.playbackSpeed);
    this._syncPlayButton();
    await this._delay(600);
    while (!run.stopped && token === this.loadToken && run.index < result.actions.length) {
      if (run.paused) { await this._delay(80); continue; }
      const action = result.actions[run.index];
      const prev = this.state;
      const next = result.states[run.index + 1];
      this.busy = true;
      const moved = action === "SWITCH_CONTROL" ? next : (await api.step(this.level.id, prev, action)).moved;
      if (token !== this.loadToken) break;
      if (run.stopped) { this.busy = false; break; }
      if (!(await this._applyMove(prev, action, { state: next, moved }, token))) break;
      this.busy = false;
      run.index++;
      await wait(70);
    }
    if (this.playing === run) this.playing = null;
    setSpeed(1);
    this._syncPlayButton();
    if (!run.stopped && token === this.loadToken && run.index === result.actions.length) await this._win({ advance: false });
  }

  stopPlayback() {
    if (this.playing) {
      this.playing.stopped = true;
      this.playing = null;
    }
    setSpeed(1);
    this._syncPlayButton();
  }

  togglePause() {
    if (this.playing) {
      this.playing.paused = !this.playing.paused;
    } else if (this.result) {
      this.play(this.result);
      return;
    }
    this._syncPlayButton();
  }

  _syncPlayButton() {
    const b = $("btn-play");
    const running = this.playing && !this.playing.paused;
    b.textContent = running ? "❚❚" : "▶";
    b.setAttribute("aria-label", running ? "Pause" : this.playing ? "Resume" : "Replay");
  }

  _applySearchLayer(result) {
    this.board.showHeat(result.explored, this.level.start);
    this.board.showPath(result.states);
    this.board.setSearchVisible($("chk-heat").checked);
  }

  // ---------- HUD ----------

  _buildHud() {
    const pick = $("solver-pick");
    for (const s of this.options.solvers) {
      const b = document.createElement("button");
      b.textContent = s.name;
      b.setAttribute("role", "radio");
      b.addEventListener("click", () => this._selectSolver(s.name));
      pick.appendChild(b);
    }
    const fill = (sel, values, saved) => {
      for (const v of values) {
        const o = document.createElement("option");
        o.value = v;
        o.textContent = v.toLowerCase().replace(/_/g, " ").replace(/^./, ch => ch.toUpperCase());
        sel.appendChild(o);
      }
      if (values.includes(saved)) sel.value = saved;
    };
    fill($("sel-cost"), this.options.costs, store.get("cost", "RISK_AWARE"));
    fill($("sel-heuristic"), this.options.heuristics, store.get("heuristic", this.options.heuristics.at(-1)));
    $("sel-cost").addEventListener("change", e => store.set("cost", e.target.value));
    $("sel-heuristic").addEventListener("change", e => store.set("heuristic", e.target.value));
    this._selectSolver(this.options.solvers.some(s => s.name === this.solver) ? this.solver : "A*");

    $("btn-solve").addEventListener("click", () => this.solve());
    $("btn-compare").addEventListener("click", () => this.compare());
    $("btn-play").addEventListener("click", () => this.togglePause());
    const speed = $("speed");
    // the speed slider only affects solver playback; manual moves always run at normal speed
    const applySpeed = () => {
      this.playbackSpeed = Number(speed.value);
      if (this.playing) setSpeed(this.playbackSpeed);
      $("speed-out").textContent = `${speed.value}×`;
    };
    speed.addEventListener("input", applySpeed);
    applySpeed();
    $("chk-heat").addEventListener("change", e => this.board?.setSearchVisible(e.target.checked));

    $("btn-restart").addEventListener("click", () => !this.busy && this.restart());
    $("btn-levels").addEventListener("click", () => this._openLevels());
    $("btn-help").addEventListener("click", () => this._open("ov-help"));
    $("btn-next").addEventListener("click", () => {
      this._close("ov-win");
      const next = this.levels[(this.levelIndex + 1) % this.levels.length];
      this.load(next.id);
    });
    $("btn-replay").addEventListener("click", () => { this._close("ov-win"); this.load(this.level.id); });
    document.querySelectorAll("[data-close]").forEach(b => b.addEventListener("click", () => this._close(b.closest(".overlay").id)));
    document.querySelectorAll(".overlay").forEach(ov => ov.addEventListener("click", e => { if (e.target === ov && ov.id !== "ov-win") this._close(ov.id); }));

    // panel: keep the board centred in the free area on wide screens; collapsible sheet on phones
    const panel = $("panel");
    const narrow = window.matchMedia("(max-width: 760px)");
    const syncInset = () => this.stage.setRightInset(narrow.matches ? 0 : panel.offsetWidth + 16);
    narrow.addEventListener("change", () => { syncInset(); this._collapse(narrow.matches); });
    syncInset();
    if (narrow.matches) this._collapse(true);
    $("panel-handle").addEventListener("click", () => narrow.matches && this._collapse(!panel.classList.contains("collapsed")));

    $("dpad").addEventListener("click", e => {
      const dir = e.target.closest("button")?.dataset.dir;
      if (!dir) return;
      this.request(dir === "swap" ? "SWITCH_CONTROL" : this.screenToAction(dir));
    });
  }

  _buildThemes() {
    const dock = $("themes");
    for (const t of THEMES) {
      const b = document.createElement("button");
      b.dataset.theme = t.id;
      b.setAttribute("role", "radio");
      b.setAttribute("aria-label", t.name);
      b.title = `${t.name}: ${t.note}`;
      b.style.setProperty("--swatch", `radial-gradient(circle at 35% 30%, ${t.board.glow}, ${t.block.body} 55%, ${t.board.rock})`);
      b.addEventListener("click", () => this.setTheme(t.id));
      dock.appendChild(b);
    }
    this._syncThemes();
  }

  _collapse(collapsed) {
    const panel = $("panel");
    panel.classList.toggle("collapsed", collapsed);
    $("panel-handle").setAttribute("aria-expanded", String(!collapsed));
    $("handle-state").textContent = collapsed ? "Tap to open" : "Tap to close";
  }

  _selectSolver(name) {
    this.solver = name;
    store.set("solver", name);
    const spec = this.options.solvers.find(s => s.name === name);
    for (const b of $("solver-pick").children) b.setAttribute("aria-checked", String(b.textContent === name));
    $("field-cost").classList.toggle("off", !spec.usesCost);
    $("field-heuristic").classList.toggle("off", !spec.usesHeuristic);
    $("algo-note").textContent = ALGO_NOTES[name] || "";
  }

  _setResult(result) {
    this.result = result;
    $("result").hidden = !result;
    if (!result) return;
    const m = result.metrics;
    $("m-steps").textContent = m.steps;
    $("m-cost").textContent = Number.isInteger(m.pathCost) ? m.pathCost : m.pathCost.toFixed(1);
    $("m-expanded").textContent = m.expanded.toLocaleString("en-US");
    $("m-time").innerHTML = m.timeMs < 1000 ? `${m.timeMs.toFixed(m.timeMs < 10 ? 1 : 0)}<small>ms</small>` : `${(m.timeMs / 1000).toFixed(2)}<small>s</small>`;
    $("m-mem").innerHTML = m.memoryMb < 1 ? `${Math.round(m.memoryMb * 1024)}<small>KB</small>` : `${m.memoryMb.toFixed(1)}<small>MB</small>`;
  }

  _renderCompare() {
    const rows = this.compareRows;
    const best = key => Math.min(...rows.filter(r => r.found).map(r => key(r)));
    const bests = {
      steps: best(r => r.metrics.steps),
      cost: best(r => r.metrics.pathCost),
      expanded: best(r => r.metrics.expanded),
      time: best(r => r.metrics.timeMs),
    };
    const body = $("compare-body");
    body.innerHTML = "";
    rows.forEach(r => {
      const tr = document.createElement("tr");
      const m = r.metrics;
      const cell = (value, isBest) => `<td class="${isBest ? "best" : ""}">${value}</td>`;
      tr.innerHTML = `<td>${r.solver}</td>`
        + cell(r.found ? m.steps : "–", r.found && m.steps === bests.steps)
        + cell(r.found ? m.pathCost : "–", r.found && m.pathCost === bests.cost)
        + cell(m.expanded.toLocaleString("en-US"), m.expanded === bests.expanded)
        + cell(`${m.timeMs < 10 ? m.timeMs.toFixed(1) : Math.round(m.timeMs)} ms`, m.timeMs === bests.time);
      tr.tabIndex = 0;
      const pickRow = () => {
        body.querySelectorAll("tr").forEach(x => x.classList.toggle("on", x === tr));
        this._setResult(r);
        this.play(r);
      };
      tr.addEventListener("click", pickRow);
      tr.addEventListener("keydown", e => { if (e.key === "Enter") pickRow(); });
      body.appendChild(tr);
    });
  }

  _setMoves(n) {
    this.moves = n;
    $("moves").textContent = n;
  }

  _showPar() {
    const best = this.par.get(this.level?.id);
    $("par").hidden = best === undefined;
    if (best !== undefined) $("par-value").textContent = best;
  }

  _openLevels() {
    const grid = $("level-grid");
    grid.innerHTML = "";
    for (const lv of this.levels) {
      const b = document.createElement("button");
      b.textContent = lv.number;
      b.className = [lv.id === this.level?.id ? "current" : "", this.done.has(lv.id) ? "done" : ""].join(" ").trim();
      b.setAttribute("aria-label", `Level ${lv.number}${this.done.has(lv.id) ? ", cleared" : ""}`);
      b.addEventListener("click", () => { this._close("ov-levels"); this.load(lv.id); });
      grid.appendChild(b);
    }
    this._open("ov-levels");
    grid.querySelector(".current")?.focus();
  }

  _open(id) {
    this._lastFocus = document.activeElement;
    $(id).hidden = false;
  }

  _close(id) {
    $(id).hidden = true;
    this._lastFocus?.focus?.();
  }

  _toast(text, bad = false) {
    const t = $("toast");
    t.textContent = text;
    t.classList.toggle("bad", bad);
    t.classList.add("show");
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => t.classList.remove("show"), 2200);
  }

  _bindKeys() {
    const keyDir = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right", w: "up", s: "down", a: "left", d: "right" };
    window.addEventListener("keydown", e => {
      if (e.target.closest?.("select, input")) return;
      const openOverlay = document.querySelector(".overlay:not([hidden])");
      if (e.key === "Escape" && openOverlay && openOverlay.id !== "ov-win") { this._close(openOverlay.id); return; }
      if (openOverlay) return;
      const dir = keyDir[e.key] || keyDir[e.key.toLowerCase?.()];
      if (dir) { e.preventDefault(); this.request(this.screenToAction(dir)); return; }
      if (e.key === " ") { e.preventDefault(); this.request("SWITCH_CONTROL"); return; }
      const k = e.key.toLowerCase();
      if (k === "r" && !this.busy) this.restart();
      else if (k === "n") this._openLevels();
      else if (k === "h" || e.key === "?") this._open("ov-help");
      else if (k === "c") this.stage.resetView();
      else if (k === "t") {
        const i = THEMES.indexOf(this.theme);
        this.setTheme(THEMES[(i + (e.shiftKey ? THEMES.length - 1 : 1)) % THEMES.length].id);
      }
    });
  }
}

const game = new Game();
window.bloxorz = game; // handy for debugging in the browser console
game.boot();
