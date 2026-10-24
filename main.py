from typing import Any

from ursina import Ursina, Vec3, color, window, application

from ursina.shaders import lit_with_shadows_shader

from src.gui.controller.controller import GameController

app: Any = Ursina(
    title="Bloxorz Game",
    fullscreen=False,
    editor_ui_enabled=False,
    development_mode=False,
)


controller = GameController(max_levels=33)


def update() -> None:
    controller.update()


def input(key: str) -> None:
    controller.handle_input(key)


app.run()
