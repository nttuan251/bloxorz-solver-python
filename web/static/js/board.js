// The floating island: tiles, bridges, switches, the goal, plus the search heat overlay.
import * as THREE from "three";
import { ease, tween, wait } from "./tween.js";
import { beamTexture, crackTexture, glowTexture, hash2, plankTexture, roundedBox } from "./geometry.js";

const SLAB_H = 0.34;
// the theme's board colours (themes.js) as THREE.Color objects
const palette = board => Object.fromEntries(Object.entries(board).map(([k, v]) => [k, new THREE.Color(v)]));

// shared geometry, built once
const GEO = {
  slab: roundedBox(0.95, SLAB_H, 0.95, 0.07, 3).translate(0, -SLAB_H / 2, 0),
  rock: new THREE.CylinderGeometry(0.64, 0.1, 1, 4, 1).rotateY(Math.PI / 4),
  top: new THREE.PlaneGeometry(0.9, 0.9).rotateX(-Math.PI / 2),
  hole: new THREE.PlaneGeometry(0.72, 0.72).rotateX(-Math.PI / 2),
  beam: new THREE.CylinderGeometry(0.36, 0.36, 2.4, 4, 1, true).rotateY(Math.PI / 4),
  button: new THREE.CylinderGeometry(0.27, 0.3, 0.07, 40),
  bar: roundedBox(0.62, 0.07, 0.15, 0.03, 2),
  half: new THREE.CylinderGeometry(0.27, 0.3, 0.07, 24, 1, false, 0, Math.PI),
  dot: new THREE.CircleGeometry(0.11, 20).rotateX(-Math.PI / 2),
  chunk: roundedBox(0.3, 0.2, 0.3, 0.04, 1),
};

// the plank texture is painted in the original brown (#a87c54); divide it out so the theme's wood colour shows
const PLANK_BASE = new THREE.Color("#a87c54");
export const plankTint = wood => new THREE.Color(
  Math.min(1, wood.r / PLANK_BASE.r), Math.min(1, wood.g / PLANK_BASE.g), Math.min(1, wood.b / PLANK_BASE.b));

function stoneMaterial(color, rough = 0.88) {
  return new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0 });
}

export class Board {
  constructor(stage, level) {
    this.stage = stage;
    this.level = level;
    this.colors = palette(stage.theme.board);
    this.root = new THREE.Group();
    stage.scene.add(this.root);
    this.offset = { x: (level.cols - 1) / 2, z: (level.rows - 1) / 2 };
    this.tiles = new Map(); // "r,c" -> { group, type, ... }
    this.bridgeOpen = new Map();
    this.heat = new THREE.Group();
    this.path = new THREE.Group();
    this.root.add(this.heat, this.path);
    this.materials = [];
    this._build();
    this._frameHandler = now => this._animate(now);
    stage.onFrame.add(this._frameHandler);
  }

  world(r, c) {
    return new THREE.Vector3(c - this.offset.x, 0, r - this.offset.z);
  }

  _mat(m) { this.materials.push(m); return m; }

  _build() {
    const stone = this._mat(stoneMaterial(this.colors.stone));
    const rock = this._mat(new THREE.MeshStandardMaterial({ color: this.colors.rock, roughness: 1, flatShading: true }));
    const fragile = this._mat(stoneMaterial(this.colors.fragile, 0.8));
    const wood = this._mat(new THREE.MeshStandardMaterial({ color: this.colors.wood, roughness: 0.9 }));
    const brass = this._mat(new THREE.MeshStandardMaterial({ color: this.colors.brass, roughness: 0.32, metalness: 0.55 }));
    const crack = this._mat(new THREE.MeshBasicMaterial({ map: crackTexture, transparent: true, depthWrite: false }));
    const planks = this._mat(new THREE.MeshStandardMaterial({ map: plankTexture, color: plankTint(this.colors.wood), roughness: 0.9 }));
    const hole = this._mat(new THREE.MeshBasicMaterial({ color: this.colors.hole }));

    for (const { r, c, type } of this.level.tiles) {
      const g = new THREE.Group();
      g.position.copy(this.world(r, c));
      const tile = { group: g, type, r, c };
      const jitter = hash2(r, c);

      if (type === "BRIDGE") {
        const slab = new THREE.Mesh(GEO.slab, wood);
        slab.scale.set(1, 0.7, 1);
        slab.castShadow = slab.receiveShadow = true;
        const top = new THREE.Mesh(GEO.top, planks);
        top.position.y = 0.002;
        top.receiveShadow = true;
        g.add(slab, top);
      } else {
        // each tile gets its own tint so the stone looks natural, not printed
        const tint = type === "FRAGILE" ? fragile : stone.clone();
        if (type !== "FRAGILE") {
          tint.color.offsetHSL(0, (jitter - 0.5) * 0.04, (jitter - 0.5) * 0.05);
          this._mat(tint);
        }
        const slab = new THREE.Mesh(GEO.slab, tint);
        slab.castShadow = slab.receiveShadow = true;
        g.add(slab);

        // jagged rock underneath turns the grid into a floating island
        const depth = 0.5 + hash2(c * 3.1, r * 1.7) * 1.4;
        const under = new THREE.Mesh(GEO.rock, rock);
        under.scale.set(1, depth, 1);
        under.position.y = -SLAB_H - depth / 2 + 0.02;
        under.rotation.y = (jitter - 0.5) * 0.3;
        g.add(under);

        if (type === "FRAGILE") {
          const top = new THREE.Mesh(GEO.top, crack);
          top.position.y = 0.003;
          top.rotation.y = Math.floor(jitter * 4) * (Math.PI / 2);
          g.add(top);
        }
        if (type === "GOAL") this._goal(g, hole);
        if (type.endsWith("SWITCH")) tile.button = this._switch(g, type, brass);
      }

      this.root.add(g);
      this.tiles.set(`${r},${c}`, tile);
    }
  }

  _goal(g, holeMat) {
    const hole = new THREE.Mesh(GEO.hole, holeMat);
    hole.position.y = 0.003;
    const glow = new THREE.Mesh(GEO.hole, new THREE.MeshBasicMaterial({
      map: glowTexture, color: this.colors.glow, transparent: true, opacity: 0.85,
      blending: THREE.AdditiveBlending, depthWrite: false,
    }));
    glow.position.y = 0.006;
    glow.scale.setScalar(0.9);
    const beam = new THREE.Mesh(GEO.beam, new THREE.MeshBasicMaterial({
      map: beamTexture, color: this.colors.beam, transparent: true, opacity: 0.4,
      blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
    }));
    beam.position.y = 1.2;
    const light = new THREE.PointLight(this.colors.light, 3, 3.5, 1.6);
    light.position.y = 0.35;
    g.add(hole, glow, beam, light);
    this.goalParts = { glow, beam, light };
  }

  _switch(g, type, brass) {
    const btn = new THREE.Group();
    if (type === "SOFT_SWITCH") {
      btn.add(new THREE.Mesh(GEO.button, brass));
    } else if (type === "HEAVY_SWITCH") {
      for (const a of [Math.PI / 4, -Math.PI / 4]) {
        const bar = new THREE.Mesh(GEO.bar, brass);
        bar.rotation.y = a;
        btn.add(bar);
      }
    } else {
      for (const side of [-1, 1]) {
        const half = new THREE.Mesh(GEO.half, brass);
        half.rotation.y = side > 0 ? 0 : Math.PI;
        half.position.x = side * 0.06;
        btn.add(half);
      }
    }
    btn.traverse(o => { o.castShadow = true; o.receiveShadow = true; });
    btn.position.y = 0.035;
    g.add(btn);
    return btn;
  }

  _animate(now) {
    if (!this.goalParts) return;
    const p = 0.5 + 0.5 * Math.sin(now * 0.0022);
    this.goalParts.beam.material.opacity = 0.22 + p * 0.25;
    this.goalParts.glow.material.opacity = 0.6 + p * 0.35;
    this.goalParts.light.intensity = 2.2 + p * 1.4;
  }

  // ---------- entrance and exit ----------

  async enter() {
    const jobs = [];
    for (const tile of this.tiles.values()) {
      const g = tile.group;
      const home = g.position.y;
      const delay = (tile.r + tile.c) * 28 + hash2(tile.r, tile.c) * 120;
      g.position.y = home - 9;
      g.scale.setScalar(0.7);
      jobs.push(tween({
        duration: 700, delay, easing: ease.outBack, scale: false,
        update: k => { g.position.y = home - 9 * (1 - k); g.scale.setScalar(0.7 + 0.3 * k); },
      }));
    }
    await Promise.all(jobs);
  }

  async exit() {
    const jobs = [];
    for (const tile of this.tiles.values()) {
      const g = tile.group;
      if (!g.visible) continue;
      const y0 = g.position.y;
      const delay = (tile.r + tile.c) * 18;
      jobs.push(tween({
        duration: 520, delay, easing: ease.inBack, scale: false,
        update: k => { g.position.y = y0 - 12 * k; },
      }));
    }
    await Promise.all(jobs);
  }

  // ---------- bridges ----------

  /** Show bridges as in `bridges` ([[r, c, open], ...]). Returns the coords that changed. */
  async setBridges(bridges, animate = true) {
    const changed = [];
    const jobs = [];
    for (const [r, c, open] of bridges) {
      const key = `${r},${c}`;
      const tile = this.tiles.get(key);
      if (!tile) continue;
      const was = this.bridgeOpen.get(key);
      this.bridgeOpen.set(key, open);
      if (was === open) continue;
      if (was !== undefined) changed.push({ r, c, open });
      const g = tile.group;
      if (!animate || was === undefined) {
        g.visible = open;
        g.position.y = 0;
        g.scale.set(1, 1, 1);
        continue;
      }
      if (open) {
        g.visible = true;
        jobs.push(tween({
          duration: 420, easing: ease.outBack,
          update: k => { g.position.y = -1.4 * (1 - k); g.scale.set(0.6 + 0.4 * k, k, 0.6 + 0.4 * k); },
        }));
      } else {
        jobs.push(tween({
          duration: 320, easing: ease.inQuad,
          update: k => { g.position.y = -1.4 * k; g.scale.set(1 - 0.4 * k, 1 - k * 0.99, 1 - 0.4 * k); },
        }).then(() => { g.visible = !this.bridgeOpen.get(key) ? false : g.visible; }));
      }
    }
    await Promise.all(jobs);
    return changed;
  }

  isBridgeOpen(r, c) {
    return this.bridgeOpen.get(`${r},${c}`) !== false;
  }

  // ---------- switches and fragile tiles ----------

  async press(r, c) {
    const tile = this.tiles.get(`${r},${c}`);
    if (!tile?.button) return;
    const b = tile.button;
    await tween({ duration: 110, update: k => { b.position.y = 0.035 - 0.05 * k; } });
    await tween({ duration: 260, easing: ease.outBack, update: k => { b.position.y = -0.015 + 0.05 * k; } });
  }

  isSwitch(r, c) {
    return Boolean(this.tiles.get(`${r},${c}`)?.button);
  }

  async shatter(r, c) {
    const tile = this.tiles.get(`${r},${c}`);
    if (!tile) return;
    const g = tile.group;
    const mat = g.children[0].material;
    g.visible = false;
    const pieces = [];
    for (let i = 0; i < 9; i++) {
      const m = new THREE.Mesh(GEO.chunk, mat);
      const ox = ((i % 3) - 1) * 0.31;
      const oz = (Math.floor(i / 3) - 1) * 0.31;
      m.position.set(g.position.x + ox, -0.1, g.position.z + oz);
      m.castShadow = true;
      this.root.add(m);
      pieces.push({ m, ox, oz, spin: new THREE.Vector3(Math.random() * 6, Math.random() * 6, Math.random() * 6) });
    }
    await tween({
      duration: 900, easing: ease.inQuad,
      update: k => {
        for (const p of pieces) {
          p.m.position.y = -0.1 - 9 * k;
          p.m.position.x = g.position.x + p.ox * (1 + 2 * k);
          p.m.position.z = g.position.z + p.oz * (1 + 2 * k);
          p.m.rotation.set(p.spin.x * k, p.spin.y * k, p.spin.z * k);
        }
      },
    });
    for (const p of pieces) this.root.remove(p.m);
  }

  restoreTiles() {
    for (const tile of this.tiles.values()) {
      if (tile.type !== "BRIDGE") tile.group.visible = true;
      tile.group.position.y = 0;
    }
  }

  // ---------- search visualisation ----------

  clearSearch() {
    for (const group of [this.heat, this.path]) {
      for (const child of [...group.children]) {
        child.material.dispose();
        group.remove(child);
      }
    }
  }

  /**
   * Tint every tile by how many expanded states touched it. The wave starts at the
   * start tile and spreads outwards, which reads like the search frontier growing.
   */
  async showHeat(explored, start) {
    this.clearSearch();
    if (!explored.length) return;
    const max = Math.max(...explored.map(e => e[2]));
    const jobs = [];
    for (const [r, c, n] of explored) {
      const t = Math.log1p(n) / Math.log1p(max);
      const mat = new THREE.MeshBasicMaterial({
        // three stops so "a few visits" and "many visits" read as different colours, not shades
        color: t < 0.5
          ? this.colors.heatLow.clone().lerp(this.colors.heatMid, t * 2)
          : this.colors.heatMid.clone().lerp(this.colors.heatHigh, t * 2 - 1),
        transparent: true, opacity: 0, depthWrite: false,
      });
      const plane = new THREE.Mesh(GEO.top, mat);
      plane.position.copy(this.world(r, c));
      plane.position.y = this.tiles.get(`${r},${c}`)?.type === "BRIDGE" ? 0.006 : 0.004;
      plane.renderOrder = 2;
      this.heat.add(plane);
      const dist = Math.abs(r - start[0]) + Math.abs(c - start[1]);
      const target = 0.55 + 0.4 * t;
      jobs.push(tween({ duration: 380, delay: dist * 45, scale: false, update: k => { mat.opacity = target * k; } }));
    }
    await Promise.all(jobs);
  }

  /** Gold dots along the cells covered by the solution. */
  showPath(states) {
    for (const child of [...this.path.children]) { child.material.dispose(); this.path.remove(child); }
    const seen = new Set();
    states.forEach((s, i) => {
      for (const [r, c] of [s.a, s.b]) {
        const key = `${r},${c}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const mat = new THREE.MeshBasicMaterial({ color: this.colors.path, transparent: true, opacity: 0, depthWrite: false });
        const dot = new THREE.Mesh(GEO.dot, mat);
        dot.position.copy(this.world(r, c));
        dot.position.y = 0.012;
        dot.renderOrder = 3;
        this.path.add(dot);
        tween({ duration: 240, delay: 300 + i * 30, scale: false, update: k => { mat.opacity = 0.9 * k; } });
      }
    });
  }

  setSearchVisible(visible) {
    this.heat.visible = visible;
    this.path.visible = visible;
  }

  dispose() {
    this.stage.onFrame.delete(this._frameHandler);
    this.clearSearch();
    this.stage.scene.remove(this.root);
    this.root.traverse(o => {
      if (o.isMesh && o.material && !this.materials.includes(o.material)) o.material.dispose?.();
    });
    for (const m of this.materials) m.dispose();
  }
}

export { wait };
