from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ursina import Entity, Vec3, curve, destroy, invoke, scene

Callback = Callable[[], None]

_FALL_DISTANCE = 10
_FALL_DURATION = 0.6


class AnimationGate:
    def __init__(self) -> None:
        self.busy = False
        self._closed = False

    def begin(self) -> None:
        self.busy = True

    def close(self) -> None:
        self._closed = True
        self.busy = False

    def schedule(self, delay: float, action: Callback) -> None:
        def run() -> None:
            if not self._closed:
                action()

        invoke(run, delay=delay)

    def finish_after(
        self,
        delay: float,
        on_done: Callback | None = None,
        cleanup: Callback | None = None,
    ) -> None:
        self.busy = True

        def finish() -> None:
            if cleanup:
                cleanup()
            self.busy = False
            if on_done:
                on_done()

        self.schedule(delay, finish)


def stop_animations(entity: Entity) -> None:
    animations: Any = getattr(entity, "animations", None)
    if animations is None:
        return
    running = (
        list(animations.values()) if isinstance(animations, dict) else list(animations)
    )
    for animation in running:
        animation.kill()
    animations.clear()


def destroy_entity(entity: Entity) -> None:
    stop_animations(entity)
    destroy(entity)


def attach_pivot(
    entity: Entity,
    position: Vec3,
    rotation: Vec3,
    duration: float,
    easing=curve.in_out_quad,
) -> Entity:
    pivot = Entity(position=position)
    entity.world_parent = pivot
    pivot.animate_rotation(rotation, duration=duration, curve=easing)
    return pivot


def release_pivot(entity: Entity, pivot: Entity) -> None:
    entity.world_parent = scene
    destroy_entity(pivot)


def sink_into_void(
    entity: Entity, gate: AnimationGate, on_finish: Callback | None
) -> None:
    entity.animate_position(
        entity.position + Vec3(0, -_FALL_DISTANCE, 0),
        duration=_FALL_DURATION,
        curve=curve.in_quad,
    )
    gate.finish_after(_FALL_DURATION + 0.05, on_finish)
