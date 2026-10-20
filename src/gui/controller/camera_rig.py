"""Camera pivot: follow target, drag-rotate, zoom."""

from __future__ import annotations

from ursina import Entity, Vec3, camera, lerp, mouse, time
from ursina.input_handler import held_keys

from src.gui import config


def frame_dt() -> float:
    return float(getattr(time, "dt", 0.0))


class CameraRig:
    def __init__(self) -> None:
        self.target_fov: float = config.CAMERA_FOV
        self.pivot = Entity()
        camera.orthographic = config.CAMERA_ORTHOGRAPHIC
        camera.parent = self.pivot
        camera.position = config.CAMERA_OFFSET
        camera.rotation = config.CAMERA_ROT
        camera.fov = config.CAMERA_FOV

    def snap_to(self, position: Vec3) -> None:
        self.pivot.position = position

    def handle_scroll(self, key: str) -> bool:
        if key == "scroll up":
            self.target_fov = max(config.MIN_FOV, self.target_fov - config.ZOOM_STEP)
            return True
        if key == "scroll down":
            self.target_fov = min(config.MAX_FOV, self.target_fov + config.ZOOM_STEP)
            return True
        return False

    def update(self, follow: Vec3 | None) -> None:
        dt = frame_dt()

        if follow is not None:
            self.pivot.position = lerp(
                self.pivot.position, follow, dt * config.CAMERA_SPEED
            )

        if held_keys["left mouse"]:
            self.pivot.rotation_y += mouse.velocity[0] * config.MOUSE_SENSITIVITY
            self.pivot.rotation_x -= mouse.velocity[1] * config.MOUSE_SENSITIVITY
        else:
            self.pivot.rotation = lerp(
                self.pivot.rotation, Vec3(0, 0, 0), dt * config.RESET_SPEED
            )

        camera.fov = lerp(camera.fov, self.target_fov, dt * config.ZOOM_SPEED)
