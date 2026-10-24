// Fireworks over the goal when a level is cleared: rockets rise from the hole, burst into
// sparks that fall under gravity and fade. Plain CPU particles, one Points object per show.
import * as THREE from "three";
import { glowTexture } from "./geometry.js";

const SPARKS = 180;
const GRAVITY = -5.5;

export function fireworks(stage, origin, colors, { bursts = 6, duration = 2600 } = {}) {
  const total = bursts * (SPARKS + 1);
  const pos = new Float32Array(total * 3);
  const col = new Float32Array(total * 3);
  const base = new Float32Array(total * 3); // each spark keeps its own colour
  const vel = new Float32Array(total * 3);
  const born = new Float32Array(total).fill(Infinity); // when each particle starts to show
  const life = new Float32Array(total);
  const palette = colors.map(c => new THREE.Color(c));

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  const mat = new THREE.PointsMaterial({
    size: 0.5, map: glowTexture, vertexColors: true, transparent: true,
    depthWrite: false, blending: THREE.AdditiveBlending,
  });
  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;
  stage.scene.add(points);

  // each burst: a rocket (index b*(SPARKS+1)) then its sparks
  const plan = [];
  for (let b = 0; b < bursts; b++) {
    plan.push({
      at: b * (duration * 0.55 / bursts) + Math.random() * 120,
      from: origin.clone().add(new THREE.Vector3((Math.random() - 0.5) * 1.2, 0.2, (Math.random() - 0.5) * 1.2)),
      to: origin.clone().add(new THREE.Vector3((Math.random() - 0.5) * 6, 4.5 + Math.random() * 3, (Math.random() - 0.5) * 6)),
      color: palette[b % palette.length],
      second: palette[(b + 1) % palette.length],
      exploded: false,
    });
  }

  const start = performance.now();
  let last = start;
  return new Promise(resolve => {
    const step = now => {
      const t = now - start;
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      plan.forEach((p, b) => {
        const r = b * (SPARKS + 1);
        const rise = 520;
        if (t >= p.at && t < p.at + rise) {
          // rocket climbing with a slight ease-out
          const k = 1 - Math.pow(1 - (t - p.at) / rise, 2);
          pos.set([p.from.x + (p.to.x - p.from.x) * k, p.from.y + (p.to.y - p.from.y) * k, p.from.z + (p.to.z - p.from.z) * k], r * 3);
          col.set([1, 0.95, 0.85], r * 3);
        } else if (t >= p.at + rise && !p.exploded) {
          p.exploded = true;
          col.set([0, 0, 0], r * 3);
          const v = new THREE.Vector3();
          for (let i = 1; i <= SPARKS; i++) {
            const j = r + i;
            v.randomDirection().multiplyScalar(2.6 + Math.random() * 1.6);
            pos.set([p.to.x, p.to.y, p.to.z], j * 3);
            vel.set([v.x, v.y + 0.8, v.z], j * 3);
            born[j] = t;
            life[j] = 1100 + Math.random() * 700;
            const c = Math.random() < 0.7 ? p.color : p.second;
            base.set([c.r, c.g, c.b], j * 3);
          }
        }
        if (!p.exploded) return;
        for (let i = 1; i <= SPARKS; i++) {
          const j = r + i;
          const age = t - born[j];
          if (age < 0) continue;
          const fade = Math.max(0, 1 - age / life[j]);
          vel[j * 3 + 1] += GRAVITY * dt;
          for (let a = 0; a < 3; a++) {
            vel[j * 3 + a] *= 0.985; // air drag
            pos[j * 3 + a] += vel[j * 3 + a] * dt;
          }
          // twinkle while fading out
          const flicker = fade * (0.6 + 0.4 * Math.sin(age * 0.05 + j));
          for (let a = 0; a < 3; a++) col[j * 3 + a] = base[j * 3 + a] * flicker;
        }
      });
      geo.attributes.position.needsUpdate = true;
      geo.attributes.color.needsUpdate = true;
      if (t > duration + 1800) {
        stage.onFrame.delete(step);
        stage.scene.remove(points);
        geo.dispose();
        mat.dispose();
        resolve();
      }
    };
    stage.onFrame.add(step);
  });
}
