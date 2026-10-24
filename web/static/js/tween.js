// Tiny tween runner driven by the render loop. Every tween returns a promise,
// so animations read top to bottom with await.

const active = new Set();
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let speed = 1;

export const ease = {
  linear: t => t,
  inQuad: t => t * t,
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inOutCubic: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  outBack: t => {
    const c1 = 1.5, c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  },
  inBack: t => 2.2 * t * t * t - 1.2 * t * t,
};

/** Multiplies the duration of every tween started afterwards (used by solver playback). */
export function setSpeed(value) { speed = value; }

export function tween({ duration = 300, delay = 0, easing = ease.outCubic, update, scale = true }) {
  const total = reduceMotion ? 1 : duration / (scale ? speed : 1);
  const wait = reduceMotion ? 0 : delay / (scale ? speed : 1);
  return new Promise(resolve => {
    active.add({ start: performance.now() + wait, total, easing, update, resolve });
  });
}

export const wait = (ms, scale = true) => tween({ duration: ms, scale, update: () => {} });

export function tick(now) {
  for (const t of active) {
    if (now < t.start) continue;
    const k = Math.min(1, (now - t.start) / t.total);
    t.update(t.easing(k), k);
    if (k >= 1) {
      active.delete(t);
      t.resolve();
    }
  }
}

/** Finish every running tween at once (used when the level is reset mid-animation). */
export function finishAll() {
  for (const t of active) {
    t.update(t.easing(1), 1);
    t.resolve();
  }
  active.clear();
}
