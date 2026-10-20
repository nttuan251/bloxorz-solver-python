from collections.abc import Callable, Sequence
from typing import Any, TypeAlias, TypeVar

from . import color as color
from . import curve as curve
from . import time as time
from .color import Color as Color
from .input_handler import held_keys as held_keys

class Vec2:
    x: float
    y: float
    def __init__(self, x: float = 0, y: float = 0) -> None: ...
    def __getitem__(self, index: int) -> float: ...

class Vec3:
    x: float
    y: float
    z: float
    def __init__(self, *args: float) -> None: ...
    def __getitem__(self, index: int) -> float: ...
    def __add__(self, other: Vec3Like) -> Vec3: ...
    def __sub__(self, other: Vec3Like) -> Vec3: ...
    def __mul__(self, other: float | Vec3) -> Vec3: ...

Vec2Like: TypeAlias = Vec2 | tuple[float, float]
Vec3Like: TypeAlias = Vec3 | tuple[float, float] | tuple[float, float, float]
Easing: TypeAlias = Callable[[float], float]

class Entity:
    enabled: bool
    model: Any
    texture: Any
    parent: Any
    world_parent: Any
    animations: list[Any]
    x: float
    y: float
    z: float
    world_x: float
    world_y: float
    world_z: float
    rotation_x: float
    rotation_y: float
    rotation_z: float
    color: Color
    visible: bool
    alpha: float
    name: str
    collider: Any
    children: list[Entity]
    scale_x: float
    scale_y: float
    scale_z: float

    def __init__(self, add_to_scene_entities: bool = True, **kwargs: Any) -> None: ...
    @property
    def position(self) -> Vec3: ...
    @position.setter
    def position(self, value: Vec3Like) -> None: ...
    @property
    def world_position(self) -> Vec3: ...
    @world_position.setter
    def world_position(self, value: Vec3Like) -> None: ...
    @property
    def rotation(self) -> Vec3: ...
    @rotation.setter
    def rotation(self, value: Vec3Like) -> None: ...
    @property
    def scale(self) -> Vec3: ...
    @scale.setter
    def scale(self, value: Vec3Like) -> None: ...
    def animate(
        self,
        name: str,
        value: Any,
        duration: float = 0.1,
        delay: float = 0,
        curve: Easing = ...,
        loop: bool = False,
        resolution: int | None = None,
        interrupt: str = "kill",
        time_step: float | None = None,
        auto_destroy: bool = True,
    ) -> Any: ...
    def animate_position(self, value: Vec3Like, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_rotation(self, value: Vec3Like, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_scale(self, value: Vec3Like | float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_color(self, value: Color, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_x(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_y(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_z(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_rotation_x(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_rotation_y(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_rotation_z(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_scale_x(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_scale_y(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...
    def animate_scale_z(self, value: float, duration: float = 0.1, **kwargs: Any) -> Any: ...

class Text(Entity):
    text: str

class Button(Entity):
    text: str
    on_click: Callable[[], Any] | None

class Camera(Entity):
    ui: Entity
    orthographic: bool
    fov: float

class Mouse:
    velocity: Vec2

class Ursina:
    def __init__(self, **kwargs: Any) -> None: ...
    def run(self, info: bool = True) -> None: ...

camera: Camera
mouse: Mouse
scene: Entity

_L = TypeVar("_L", float, Vec3)

def lerp(a: _L, b: _L, t: float) -> _L: ...
def destroy(entity: Any, delay: float = 0) -> None: ...
def invoke(function: Callable[..., Any], *args: Any, delay: float = 0, **kwargs: Any) -> Any: ...
