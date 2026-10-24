from ursina import Entity, camera, color

class MinimalistVoid(Entity):
    def __init__(self) -> None:
        super().__init__()

        self.background = Entity(
            parent=camera,
            model="quad",
            texture="assets/Dark_Navy_Vignette_Glow.png",
            scale=(40, 22.5),
            position=(0, 0, 80),
            color=color.white,
            unlit=True,
        )