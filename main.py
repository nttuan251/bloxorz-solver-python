# main.py
from ursina import Ursina
from src.gui.controller import GameController

app = Ursina(title="Bloxorz Game")

controller = GameController()

def update():
    controller.update()

def input(key):
    controller.handle_input(key)

app.run()