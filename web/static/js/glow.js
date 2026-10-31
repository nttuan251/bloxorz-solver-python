// Neon rim around the block: a box shell that only lights up near its edges, with a
// gradient that keeps flowing around it, plus a soft halo sprite behind it.
import * as THREE from "three";
import { glowTexture } from "./geometry.js";

const VERT = /* glsl */ `
  varying vec3 vP;
  void main() {
    vP = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const FRAG = /* glsl */ `
  uniform float uTime;
  uniform vec3 uHalf;
  uniform vec3 uColors[4];
  uniform float uStrength;
  varying vec3 vP;
  vec3 ramp(float t) {
    t = fract(t) * 4.0;
    int i = int(floor(t));
    float f = smoothstep(0.0, 1.0, fract(t));
    vec3 a = uColors[0], b = uColors[1];
    if (i == 1) { a = uColors[1]; b = uColors[2]; }
    else if (i == 2) { a = uColors[2]; b = uColors[3]; }
    else if (i == 3) { a = uColors[3]; b = uColors[0]; }
    return mix(a, b, f);
  }
  void main() {
    vec3 q = abs(vP) / uHalf;
    // on a face one coordinate is 1; the next largest one tells how close we are to an edge
    float mid = max(min(q.x, q.y), min(max(q.x, q.y), q.z));
    float edge = smoothstep(0.8, 1.0, mid) + 0.45 * smoothstep(0.4, 1.0, mid);
    float t = atan(vP.z, vP.x) / 6.28318 + vP.y * 0.22 - uTime * 0.35;
    float a = edge * uStrength;
    gl_FragColor = vec4(ramp(t) * a, a);
  }
`;

export class Glow {
  constructor(colors) {
    this.colors = colors.map(c => new THREE.Color(c));
    this.materials = [];
    this.halos = [];
  }

  /** An edge-lit shell for a box of size w x h x d (add it as a child of the body mesh). */
  shell(w, h, d) {
    const mat = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      uniforms: {
        uTime: { value: 0 },
        uHalf: { value: new THREE.Vector3(w / 2, h / 2, d / 2) },
        uColors: { value: this.colors },
        uStrength: { value: 1.7 },
      },
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    this.materials.push(mat);
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    mesh.renderOrder = 5;
    return mesh;
  }

  /** Soft coloured light that blooms around the body's silhouette. */
  halo(size) {
    const mat = new THREE.SpriteMaterial({
      map: glowTexture, transparent: true, opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.setScalar(size);
    this.halos.push(sprite);
    return sprite;
  }

  frame(now) {
    const t = now / 1000;
    for (const m of this.materials) m.uniforms.uTime.value = t;
    // halo colour walks through the same gradient, and breathes a little
    const k = (t * 0.35) % 1 * this.colors.length;
    const i = Math.floor(k);
    const c = this.colors[i].clone().lerp(this.colors[(i + 1) % this.colors.length], k - i);
    for (const h of this.halos) {
      h.material.color.copy(c);
      h.material.opacity = 0.55 + 0.15 * Math.sin(t * 2.2);
    }
  }

  dispose() {
    for (const m of this.materials) m.dispose();
    for (const h of this.halos) h.material.dispose();
  }
}
