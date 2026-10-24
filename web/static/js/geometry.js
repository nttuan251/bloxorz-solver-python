// Small geometry and texture helpers shared by the board and the block.
import * as THREE from "three";

/**
 * Box with rounded edges, centred on the origin. Same idea as three's RoundedBoxGeometry addon:
 * push every vertex of a finely segmented unit box onto a rounded shell.
 */
export function roundedBox(width, height, depth, radius = 0.06, segments = 3) {
  const seg = segments * 2 + 1;
  radius = Math.min(width / 2, height / 2, depth / 2, radius);
  const geo = new THREE.BoxGeometry(1, 1, 1, seg, seg, seg).toNonIndexed();
  const pos = geo.attributes.position;
  const nor = geo.attributes.normal;
  const inner = new THREE.Vector3(width / 2 - radius, height / 2 - radius, depth / 2 - radius);
  const half = 0.5 / seg;
  const v = new THREE.Vector3();
  const n = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    n.set(v.x - Math.sign(v.x) * half, v.y - Math.sign(v.y) * half, v.z - Math.sign(v.z) * half).normalize();
    pos.setXYZ(
      i,
      inner.x * Math.sign(v.x) + n.x * radius,
      inner.y * Math.sign(v.y) + n.y * radius,
      inner.z * Math.sign(v.z) + n.z * radius,
    );
    nor.setXYZ(i, n.x, n.y, n.z);
  }
  geo.computeBoundingSphere();
  return geo;
}

/** Deterministic pseudo-random number in [0, 1) for a tile, so the island looks the same every load. */
export function hash2(a, b) {
  const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453;
  return s - Math.floor(s);
}

function canvasTexture(size, draw) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  draw(canvas.getContext("2d"), size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

/** Hairline cracks for fragile tiles, drawn once and shared. */
export const crackTexture = canvasTexture(256, (g, s) => {
  g.clearRect(0, 0, s, s);
  g.strokeStyle = "rgba(96, 52, 18, 0.75)";
  g.lineCap = "round";
  const crack = (x, y, angle, len, width, depth) => {
    if (depth > 3 || len < 8) return;
    const x2 = x + Math.cos(angle) * len;
    const y2 = y + Math.sin(angle) * len;
    g.lineWidth = width;
    g.beginPath();
    g.moveTo(x, y);
    g.lineTo(x2, y2);
    g.stroke();
    crack(x2, y2, angle + 0.5, len * 0.62, width * 0.7, depth + 1);
    crack(x2, y2, angle - 0.6, len * 0.55, width * 0.6, depth + 1);
  };
  crack(s * 0.18, s * 0.3, 0.35, 70, 4, 0);
  crack(s * 0.82, s * 0.78, Math.PI + 0.4, 64, 3.5, 0);
});

/** Wooden planks for bridges. */
export const plankTexture = canvasTexture(256, (g, s) => {
  const planks = 4;
  for (let i = 0; i < planks; i++) {
    const shade = [0, 10, -8, 6][i];
    g.fillStyle = `rgb(${168 + shade}, ${124 + shade}, ${84 + shade})`;
    g.fillRect(0, (i * s) / planks, s, s / planks);
    g.fillStyle = "rgba(80, 50, 24, 0.55)";
    g.fillRect(0, ((i + 1) * s) / planks - 5, s, 5);
    g.fillStyle = "rgba(60, 36, 16, 0.6)";
    for (const x of [s * 0.12, s * 0.88]) {
      g.beginPath();
      g.arc(x, ((i + 0.5) * s) / planks, 5, 0, Math.PI * 2);
      g.fill();
    }
  }
});

/** Vertical fade used for the beam of light above the goal. */
export const beamTexture = canvasTexture(64, (g, s) => {
  const grad = g.createLinearGradient(0, 0, 0, s);
  grad.addColorStop(0, "rgba(255, 255, 255, 0)");
  grad.addColorStop(1, "rgba(255, 255, 255, 1)");
  g.fillStyle = grad;
  g.fillRect(0, 0, s, s);
});

/** Soft round spot for glows. */
export const glowTexture = canvasTexture(128, (g, s) => {
  const grad = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  grad.addColorStop(0, "rgba(255, 255, 255, 1)");
  grad.addColorStop(1, "rgba(255, 255, 255, 0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, s, s);
});
