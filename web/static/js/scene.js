// Renderer, lights, camera rig (drag to orbit, wheel to zoom) and the render loop.
import * as THREE from "three";
import { tick } from "./tween.js";
import { Sky } from "./sky.js";

export class Stage {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(30, 1, 0.1, 400);

    // orbit state (spherical around `target`)
    this.target = new THREE.Vector3();
    this.yaw = -0.62;
    this.pitch = 0.86;
    this.distance = 30;
    this.goal = { yaw: this.yaw, pitch: this.pitch, distance: this.distance };
    this.fitDistance = 30;
    this.rightInset = 0; // pixels covered by the solver panel, so the board centres in the free area

    this._lights();
    this.sky = new Sky(this.scene);
    this._input();

    this.onFrame = new Set();
    new ResizeObserver(() => this.resize()).observe(document.body);
    this.resize();
    this.renderer.setAnimationLoop(t => this._frame(t));
  }

  _lights() {
    const hemi = new THREE.HemisphereLight(0xffe9d6, 0x5a4f86, 1.25);
    this.hemi = hemi;
    this.scene.add(hemi);

    const sun = new THREE.DirectionalLight(0xffd7b0, 2.4);
    sun.position.set(-9, 16, 11);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.bias = -0.0004;
    sun.shadow.normalBias = 0.02;
    sun.shadow.radius = 5;
    this.sun = sun;
    this.scene.add(sun, sun.target);

    // cool rim light from behind so the block separates from the warm sky
    const rim = new THREE.DirectionalLight(0x9fb2ff, 0.9);
    rim.position.set(10, 6, -12);
    this.rim = rim;
    this.scene.add(rim);
  }

  /** Recolour lights and sky for a theme from themes.js. */
  applyTheme(theme) {
    this.theme = theme;
    this.renderer.toneMappingExposure = theme.exposure;
    this.hemi.color.set(theme.hemi[0]);
    this.hemi.groundColor.set(theme.hemi[1]);
    this.hemi.intensity = theme.hemi[2];
    this.sun.color.set(theme.sun[0]);
    this.sun.intensity = theme.sun[1];
    this.rim.color.set(theme.rim[0]);
    this.rim.intensity = theme.rim[1];
    this.sky.apply(theme);
  }

  _input() {
    const el = this.canvas;
    let drag = null;
    el.addEventListener("pointerdown", e => {
      drag = { x: e.clientX, y: e.clientY, yaw: this.goal.yaw, pitch: this.goal.pitch };
      el.setPointerCapture(e.pointerId);
    });
    el.addEventListener("pointermove", e => {
      if (!drag) return;
      this.goal.yaw = drag.yaw - (e.clientX - drag.x) * 0.006;
      this.goal.pitch = THREE.MathUtils.clamp(drag.pitch + (e.clientY - drag.y) * 0.005, 0.35, 1.38);
    });
    const end = () => { drag = null; };
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
    el.addEventListener("wheel", e => {
      e.preventDefault();
      const f = Math.exp(e.deltaY * 0.0012);
      this.goal.distance = THREE.MathUtils.clamp(this.goal.distance * f, this.fitDistance * 0.45, this.fitDistance * 1.8);
    }, { passive: false });
    el.addEventListener("dblclick", () => this.resetView());
  }

  /** Frame a board of `rows` x `cols` tiles centred on the origin. */
  frame(rows, cols) {
    const radius = Math.hypot(rows, cols) / 2 + 1.2;
    const aspect = Math.max(0.5, (this.width - this.rightInset) / this.height);
    const vfov = THREE.MathUtils.degToRad(this.camera.fov);
    const byHeight = radius / Math.sin(vfov / 2);
    const byWidth = radius / Math.sin(Math.atan(Math.tan(vfov / 2) * aspect));
    this.fitDistance = Math.max(byHeight, byWidth) * 0.92;
    this.target.set(0, -0.4, 0);
    this.goal.distance = this.fitDistance;

    const s = Math.max(rows, cols) / 2 + 3;
    Object.assign(this.sun.shadow.camera, { left: -s, right: s, top: s, bottom: -s, near: 1, far: 70 });
    this.sun.shadow.camera.updateProjectionMatrix();
  }

  resetView() {
    this.goal.yaw = -0.62;
    this.goal.pitch = 0.86;
    this.goal.distance = this.fitDistance;
  }

  setRightInset(px) {
    this.rightInset = px;
    this.resize();
  }

  resize() {
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.renderer.setSize(this.width, this.height, false);
    this.camera.aspect = this.width / this.height;
    // shift the projection so the board sits in the middle of the area left of the panel
    if (this.rightInset > 0) {
      this.camera.setViewOffset(this.width, this.height, this.rightInset / 2, 0, this.width, this.height);
    } else {
      this.camera.clearViewOffset();
    }
    this.camera.updateProjectionMatrix();
  }

  /** Unit vector on the ground plane that points "away from the viewer". */
  forward() {
    return new THREE.Vector2(Math.sin(this.yaw + Math.PI), Math.cos(this.yaw + Math.PI));
  }

  _frame(now) {
    tick(now);
    const k = 0.12;
    this.yaw += (this.goal.yaw - this.yaw) * k;
    this.pitch += (this.goal.pitch - this.pitch) * k;
    this.distance += (this.goal.distance - this.distance) * k;
    const cp = Math.cos(this.pitch);
    this.camera.position.set(
      this.target.x + this.distance * cp * Math.sin(this.yaw),
      this.target.y + this.distance * Math.sin(this.pitch),
      this.target.z + this.distance * cp * Math.cos(this.yaw),
    );
    this.camera.lookAt(this.target);
    this.sky.frame(now);
    for (const fn of this.onFrame) fn(now);
    this.renderer.render(this.scene, this.camera);
  }
}
