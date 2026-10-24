// The sky: a dome of twinkling stars far away, glittering dust drifting around the island,
// the occasional shooting star (drawn in CSS behind the canvas) and, for the sunny theme,
// clouds floating around and below the island.
import * as THREE from "three";

const VERT = /* glsl */ `
  attribute float aSize;
  attribute float aPhase;
  attribute float aSpeed;
  attribute vec3 aColor;
  uniform float uTime;
  uniform float uPixelRatio;
  uniform float uNear;      // 1 = size shrinks with distance (dust), 0 = fixed size (far stars)
  uniform float uRise;      // dust drifts upward and wraps inside a box of this height
  varying vec3 vColor;
  varying float vAlpha;
  varying float vFlare;
  void main() {
    vec3 p = position;
    if (uRise > 0.0) {
      p.y = mod(p.y + uTime * aSpeed * 0.25 + 7.0, uRise) - 7.0;
      p.x += sin(uTime * 0.4 * aSpeed + aPhase) * 0.35;
      p.z += cos(uTime * 0.3 * aSpeed + aPhase) * 0.35;
    }
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    float tw = 0.5 + 0.5 * sin(uTime * aSpeed + aPhase);
    float spark = pow(tw, 10.0);                 // short bright peaks: the "glint"
    vAlpha = 0.25 + 0.6 * tw + 0.6 * spark;
    vFlare = spark * step(2.4, aSize);           // only big stars get cross flares
    vColor = aColor;
    float size = aSize * (1.0 + 0.9 * spark);
    if (uNear > 0.5) size *= 28.0 / -mv.z;
    gl_PointSize = size * uPixelRatio;
    gl_Position = projectionMatrix * mv;
  }
`;

const FRAG = /* glsl */ `
  varying vec3 vColor;
  varying float vAlpha;
  varying float vFlare;
  void main() {
    vec2 q = gl_PointCoord - 0.5;
    float d = length(q);
    float core = smoothstep(0.5, 0.0, d);
    core *= core;
    float cross = max(0.0, 1.0 - abs(q.x) * 16.0) * max(0.0, 1.0 - abs(q.y) * 2.0)
                + max(0.0, 1.0 - abs(q.y) * 16.0) * max(0.0, 1.0 - abs(q.x) * 2.0);
    float a = (core + cross * vFlare * 0.9) * vAlpha;
    if (a < 0.003) discard;
    gl_FragColor = vec4(vColor * a, a);
  }
`;

function pointsMaterial(near, rise) {
  return new THREE.ShaderMaterial({
    vertexShader: VERT,
    fragmentShader: FRAG,
    uniforms: {
      uTime: { value: 0 },
      uPixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
      uNear: { value: near ? 1 : 0 },
      uRise: { value: rise },
    },
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
}

function buildPoints(count, place, sizeOf, colors, near, rise) {
  const pos = new Float32Array(count * 3);
  const col = new Float32Array(count * 3);
  const size = new Float32Array(count);
  const phase = new Float32Array(count);
  const speed = new Float32Array(count);
  const v = new THREE.Vector3();
  const c = new THREE.Color();
  for (let i = 0; i < count; i++) {
    place(v);
    pos.set([v.x, v.y, v.z], i * 3);
    c.set(colors[i % colors.length]);
    col.set([c.r, c.g, c.b], i * 3);
    size[i] = sizeOf();
    phase[i] = Math.random() * Math.PI * 2;
    speed[i] = 0.6 + Math.random() * 2.6;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("aColor", new THREE.BufferAttribute(col, 3));
  geo.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
  geo.setAttribute("aPhase", new THREE.BufferAttribute(phase, 1));
  geo.setAttribute("aSpeed", new THREE.BufferAttribute(speed, 1));
  const pts = new THREE.Points(geo, pointsMaterial(near, rise));
  pts.frustumCulled = false;
  return pts;
}

function buildClouds() {
  const group = new THREE.Group();
  const geo = new THREE.SphereGeometry(1, 20, 14);
  const mat = new THREE.MeshStandardMaterial({
    color: "#fff3ea", emissive: "#ffc9a8", emissiveIntensity: 0.18, roughness: 1, transparent: true, opacity: 0.93,
  });
  for (let i = 0; i < 22; i++) {
    const cloud = new THREE.Group();
    const puffs = 6 + Math.floor(Math.random() * 4);
    for (let j = 0; j < puffs; j++) {
      const puff = new THREE.Mesh(geo, mat);
      const r = 0.6 + Math.random() * 0.7;
      puff.scale.set(r, r * 0.75, r);
      puff.position.set((j / (puffs - 1) - 0.5) * 3.6, Math.random() * 0.5 * r, (Math.random() - 0.5) * 1.4);
      cloud.add(puff);
    }
    // most clouds float below the island, a few higher up and further out
    const high = i % 4 === 0;
    const angle = (i / 22) * Math.PI * 2 + Math.random() * 0.3;
    const dist = (high ? 22 : 14) + Math.random() * 10;
    cloud.position.set(Math.cos(angle) * dist, high ? 1 + Math.random() * 3 : -6 + Math.random() * 3.5, Math.sin(angle) * dist);
    cloud.rotation.y = -angle + Math.PI / 2;
    cloud.scale.setScalar(0.45 + Math.random() * 0.4);
    cloud.userData.bob = Math.random() * Math.PI * 2;
    group.add(cloud);
  }
  return group;
}

export class Sky {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    scene.add(this.group);
    this.layer = document.getElementById("sky");
    this.reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    this._nextShot = 2000;
  }

  apply(theme) {
    for (const p of [...this.group.children]) { p.geometry.dispose(); p.material.dispose(); this.group.remove(p); }
    if (theme.extras === "sun" && !this.clouds) {
      this.clouds = buildClouds();
      this.scene.add(this.clouds);
    }
    if (this.clouds) this.clouds.visible = theme.extras === "sun";
    const starCount = theme.starCount ?? 3400;
    if (starCount) {
      // stars on a far dome; most are tiny, a few are big enough to flare
      this.stars = buildPoints(starCount, v => {
        v.randomDirection().multiplyScalar(150);
        if (v.y < -40) v.y = -v.y * 0.6;  // keep most stars above the horizon
      }, () => (Math.random() < 0.07 ? 2.8 + Math.random() * 2.6 : 1.1 + Math.random() * 1.6), theme.stars, false, 0);
      this.group.add(this.stars);
    } else this.stars = null;
    // glitter drifting through the island
    this.dust = buildPoints(starCount ? 520 : 260, v => {
      v.set((Math.random() - 0.5) * 46, Math.random() * 18 - 7, (Math.random() - 0.5) * 46);
    }, () => 1.2 + Math.random() * 2.4, [theme.dust, "#ffffff"], true, 18);
    this.group.add(this.dust);
    this.shots = Boolean(starCount);
  }

  frame(now) {
    const t = now / 1000;
    for (const p of this.group.children) p.material.uniforms.uTime.value = this.reduced ? 0 : t;
    if (this.stars) this.stars.rotation.y = t * 0.004;
    if (this.clouds?.visible && !this.reduced) {
      this.clouds.rotation.y = t * 0.012;
      for (const c of this.clouds.children) c.position.y += Math.sin(t * 0.5 + c.userData.bob) * 0.002;
    }
    if (this.shots && !this.reduced && now > this._nextShot) {
      this._shoot();
      this._nextShot = now + 2500 + Math.random() * 5000;
    }
  }

  _shoot() {
    if (!this.layer || document.hidden) return;
    const s = document.createElement("span");
    s.className = "shooting-star";
    s.style.left = `${10 + Math.random() * 70}%`;
    s.style.top = `${Math.random() * 40}%`;
    s.style.setProperty("--angle", `${20 + Math.random() * 25}deg`);
    s.style.animationDuration = `${0.9 + Math.random() * 0.8}s`;
    s.addEventListener("animationend", () => s.remove());
    this.layer.appendChild(s);
  }
}
