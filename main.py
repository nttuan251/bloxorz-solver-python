from typing import Any

from ursina import Ursina

from src.gui.controller.controller import GameController

app: Any = Ursina(title="Bloxorz Game")

controller = GameController(max_levels=33)


def update() -> None:
    controller.update()


def input(key: str) -> None:
    controller.handle_input(key)


app.run()
