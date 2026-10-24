// The 1x1x2 block and the two 1x1x1 cubes it splits into. Poses always come from engine
// states ({a, b, split, active}); animations only interpolate between them.
import * as THREE from "three";
import { ease, tween } from "./tween.js";
import { roundedBox } from "./geometry.js";
import { Glow } from "./glow.js";

const DIRS = {
  UP: { dx: 0, dz: -1 },
  DOWN: { dx: 0, dz: 1 },
  LEFT: { dx: -1, dz: 0 },
  RIGHT: { dx: 1, dz: 0 },
};

const sameCell = (p, q) => p && q && p[0] === q[0] && p[1] === q[1];

export class Block {
  constructor(stage, board) {
    this.stage = stage;
    this.board = board;
    this.root = new THREE.Group();
    stage.scene.add(this.root);

    const colors = stage.theme.block;
    const lacquer = new THREE.MeshPhysicalMaterial({
      color: colors.body, emissive: colors.emissive, roughness: 0.36, clearcoat: 0.8, clearcoatRoughness: 0.22,
    });
    const gold = new THREE.MeshStandardMaterial({ color: colors.inlay, roughness: 0.3, metalness: 0.6 });
    this.lacquer = lacquer;
    this.idle = new THREE.MeshPhysicalMaterial({ color: colors.idle, roughness: 0.55, clearcoat: 0.3 });

    // whole block: tall box with a gold inlay on both square ends, so its orientation is easy to read
    this.whole = new THREE.Group();
    const body = new THREE.Mesh(roundedBox(0.96, 1.96, 0.96, 0.09, 3), lacquer);
    body.castShadow = true;
    const inlayGeo = new THREE.PlaneGeometry(0.42, 0.42);
    for (const side of [1, -1]) {
      const inlay = new THREE.Mesh(inlayGeo, gold);
      inlay.rotation.x = -side * Math.PI / 2;
      inlay.position.y = side * 0.982;
      this.whole.add(inlay);
    }
    this.whole.add(body);
    this.root.add(this.whole);

    // animated neon rim so the block stands out from the board
    this.glow = new Glow(stage.theme.glow);
    this.whole.add(this.glow.shell(1.02, 2.02, 1.02), this.glow.halo(3.4));

    // split cubes
    const cubeGeo = roundedBox(0.94, 0.94, 0.94, 0.09, 3);
    this.cubes = [0, 1].map(() => {
      const m = new THREE.Mesh(cubeGeo, lacquer);
      m.castShadow = true;
      m.visible = false;
      m.userData.cell = null;
      const rim = this.glow.shell(1.0, 1.0, 1.0);
      const halo = this.glow.halo(2.2);
      m.add(rim, halo);
      m.userData.lit = [rim, halo];
      this.root.add(m);
      return m;
    });
    this._frameHandler = now => this.glow.frame(now);
    stage.onFrame.add(this._frameHandler);

    // gold ring under the cube you are steering
    this.ring = new THREE.Mesh(
      new THREE.RingGeometry(0.5, 0.58, 40).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: colors.ring, transparent: true, opacity: 0.95, depthWrite: false }),
    );
    this.ring.visible = false;
    this.ring.renderOrder = 4;
    this.root.add(this.ring);
  }

  // ---------- poses ----------

  _wholePose(state) {
    const pa = this.board.world(...state.a);
    const pb = this.board.world(...state.b);
    const pos = pa.clone().add(pb).multiplyScalar(0.5);
    const rot = new THREE.Euler();
    if (sameCell(state.a, state.b)) {
      pos.y = 0.98;
    } else {
      pos.y = 0.48;
      if (state.a[0] === state.b[0]) rot.z = Math.PI / 2; // same row: lying along x
      else rot.x = Math.PI / 2; // same column: lying along z
    }
    return { pos, rot };
  }

  _cubePos(cell) {
    const p = this.board.world(...cell);
    p.y = 0.47;
    return p;
  }

  /** Snap meshes to a state with no animation. */
  set(state) {
    this.state = state;
    this.whole.scale.setScalar(1);
    if (!state.split) {
      const { pos, rot } = this._wholePose(state);
      this.whole.position.copy(pos);
      this.whole.rotation.copy(rot);
      this.whole.visible = true;
      for (const c of this.cubes) c.visible = false;
      this.ring.visible = false;
      return;
    }
    this.whole.visible = false;
    [state.a, state.b].forEach((cell, i) => {
      const cube = this.cubes[i];
      cube.visible = true;
      cube.userData.cell = cell;
      cube.position.copy(this._cubePos(cell));
      cube.rotation.set(0, 0, 0);
      cube.scale.setScalar(1);
    });
    this._paintActive(state.active);
  }

  _paintActive(active) {
    for (const cube of this.cubes) {
      const on = sameCell(cube.userData.cell, active);
      cube.material = on ? this.lacquer : this.idle;
      for (const part of cube.userData.lit) part.visible = on; // only the cube you steer glows
      if (on) {
        this.ring.visible = true;
        this.ring.position.set(cube.position.x, 0.015, cube.position.z);
      }
    }
  }

  _activeCube(state) {
    return this.cubes.find(c => sameCell(c.userData.cell, state.active));
  }

  // ---------- animations ----------

  /** Roll the moving body one step in `action`'s direction around its bottom edge. */
  async roll(prev, action) {
    const dir = DIRS[action];
    if (!dir) return;
    const mesh = prev.split ? this._activeCube(prev) : this.whole;
    const cells = prev.split ? [prev.active] : [prev.a, prev.b];
    const pts = cells.map(cell => this.board.world(...cell));
    const minX = Math.min(...pts.map(p => p.x)) - 0.5, maxX = Math.max(...pts.map(p => p.x)) + 0.5;
    const minZ = Math.min(...pts.map(p => p.z)) - 0.5, maxZ = Math.max(...pts.map(p => p.z)) + 0.5;

    const pivot = new THREE.Object3D();
    let axis, angle;
    if (dir.dx > 0) { pivot.position.set(maxX, 0, (minZ + maxZ) / 2); axis = "z"; angle = -Math.PI / 2; }
    if (dir.dx < 0) { pivot.position.set(minX, 0, (minZ + maxZ) / 2); axis = "z"; angle = Math.PI / 2; }
    if (dir.dz > 0) { pivot.position.set((minX + maxX) / 2, 0, maxZ); axis = "x"; angle = Math.PI / 2; }
    if (dir.dz < 0) { pivot.position.set((minX + maxX) / 2, 0, minZ); axis = "x"; angle = -Math.PI / 2; }

    this.root.add(pivot);
    pivot.attach(mesh);
    const follow = prev.split && this.ring.visible;
    await tween({
      duration: 240, easing: ease.inOutCubic,
      update: k => {
        pivot.rotation[axis] = angle * k;
        if (follow) {
          const w = new THREE.Vector3();
          mesh.getWorldPosition(w);
          this.ring.position.set(w.x, 0.015, w.z);
        }
      },
    });
    this.root.attach(mesh);
    this.root.remove(pivot);
    // tiny landing settle
    const y0 = mesh.position.y;
    await tween({ duration: 90, update: k => { mesh.position.y = y0 - Math.sin(k * Math.PI) * 0.03; } });
  }

  /** After a legal move: play split, merge or control-switch transitions, then snap to `next`. */
  async settle(prev, moved, next) {
    if (!prev.split && next.split) {
      await this._split(moved, next);
    } else if (prev.split && !next.split) {
      await this._merge(moved, next);
    } else if (prev.split && next.split && !sameCell(prev.active, next.active) && sameCell(prev.a, next.a) && sameCell(prev.b, next.b)) {
      await this._moveRing(next);
    }
    this.set(next);
  }

  async _split(moved, next) {
    this.set(moved);
    const w = this.whole;
    await tween({
      duration: 280, easing: ease.inBack,
      update: k => { w.scale.set(1 - 0.85 * k, 1 - 0.85 * k, 1 - 0.85 * k); w.rotation.y = k * Math.PI; },
    });
    w.visible = false;
    w.rotation.set(0, 0, 0);
    [next.a, next.b].forEach((cell, i) => {
      const cube = this.cubes[i];
      cube.userData.cell = cell;
      cube.visible = true;
      cube.material = this.lacquer;
    });
    await Promise.all(this.cubes.map((cube, i) => {
      const p = this._cubePos(i === 0 ? next.a : next.b);
      return tween({
        duration: 420, delay: i * 90, easing: ease.outBack,
        update: k => { cube.position.set(p.x, p.y + 5 * (1 - k), p.z); cube.scale.setScalar(0.4 + 0.6 * k); },
      });
    }));
  }

  async _merge(moved, next) {
    // cubes slide together and pop into the long block
    const { pos } = this._wholePose(next);
    await Promise.all(this.cubes.map(cube => {
      const from = cube.position.clone();
      return tween({ duration: 160, update: k => { cube.position.lerpVectors(from, pos, k * 0.18); } });
    }));
    for (const c of this.cubes) c.visible = false;
    this.ring.visible = false;
    this.set(next);
    await tween({ duration: 300, easing: ease.outBack, update: k => { this.whole.scale.setScalar(0.88 + 0.12 * k); } });
  }

  async _moveRing(next) {
    const target = this._cubePos(next.active);
    const from = this.ring.position.clone();
    this._paintActive(next.active);
    await tween({ duration: 200, update: k => { this.ring.position.set(from.x + (target.x - from.x) * k, 0.015, from.z + (target.z - from.z) * k); } });
  }

  /** The move was illegal: roll into the bad pose, then tumble into the void. */
  async fall(prev, action, reason) {
    if (reason === "blocked") return this.nudge(action);
    await this.roll(prev, action);
    const mesh = prev.split ? this._activeCube(prev) : this.whole;
    this.ring.visible = false;
    const dir = DIRS[action] || { dx: 0, dz: 0 };
    const start = mesh.position.clone();
    const rot0 = mesh.rotation.clone();
    await tween({
      duration: 950, easing: ease.inQuad, scale: false,
      update: k => {
        mesh.position.set(start.x + dir.dx * k * 0.8, start.y - 14 * k, start.z + dir.dz * k * 0.8);
        mesh.rotation.set(rot0.x + dir.dz * k * 2.4, rot0.y + k * 0.6, rot0.z - dir.dx * k * 2.4);
      },
    });
  }

  async nudge(action) {
    const dir = DIRS[action];
    if (!dir) return;
    const meshes = this.state.split ? [this._activeCube(this.state)] : [this.whole];
    const starts = meshes.map(m => m.position.clone());
    await tween({
      duration: 200, scale: false,
      update: k => {
        const s = Math.sin(k * Math.PI) * 0.1;
        meshes.forEach((m, i) => m.position.set(starts[i].x + dir.dx * s, starts[i].y, starts[i].z + dir.dz * s));
      },
    });
  }

  /** Stand in the goal: sink through the hole. */
  async sink() {
    const w = this.whole;
    const y0 = w.position.y;
    await tween({ duration: 120, update: k => { w.position.y = y0 + 0.12 * k; } });
    await tween({ duration: 760, easing: ease.inQuad, scale: false, update: k => { w.position.y = y0 + 0.12 - 2.4 * k; } });
    w.visible = false;
  }

  /** Drop in from above at the start of a level. */
  async dropIn(state) {
    this.set(state);
    const meshes = state.split ? this.cubes.filter(c => c.visible) : [this.whole];
    const homes = meshes.map(m => m.position.y);
    meshes.forEach(m => { m.position.y += 7; });
    await tween({
      duration: 620, easing: ease.outBack, scale: false,
      update: k => meshes.forEach((m, i) => { m.position.y = homes[i] + 7 * (1 - k); }),
    });
  }

  /** Leave the level together with the tiles: fall when the tile underneath falls (Board.exit). */
  async exit() {
    this.ring.visible = false;
    const s = this.state;
    const parts = s.split
      ? this.cubes.filter(c => c.visible).map(c => [c, c.userData.cell])
      : this.whole.visible ? [[this.whole, s.a, s.b]] : [];
    await Promise.all(parts.map(([mesh, ...cells]) => {
      const delay = cells.reduce((sum, [r, c]) => sum + (r + c) * 18, 0) / cells.length;
      const y0 = mesh.position.y;
      return tween({ duration: 520, delay, easing: ease.inBack, scale: false, update: k => { mesh.position.y = y0 - 12 * k; } });
    }));
  }

  dispose() {
    this.stage.onFrame.delete(this._frameHandler);
    this.glow.dispose();
    this.stage.scene.remove(this.root);
  }
}
