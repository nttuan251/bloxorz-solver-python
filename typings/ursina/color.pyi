class Color:
    r: float
    g: float
    b: float
    a: float
    def __init__(self, r: float, g: float, b: float, a: float = 1.0) -> None: ...
    def tint(self, amount: float) -> Color: ...
    def invert(self) -> Color: ...

def hex(value: str) -> Color: ...
def rgb(r: float, g: float, b: float, a: float = 1.0) -> Color: ...
def rgba(r: float, g: float, b: float, a: float = 1.0) -> Color: ...
def hsv(h: float, s: float, v: float, a: float = 1.0) -> Color: ...
def random_color() -> Color: ...

white: Color
smoke: Color
light_gray: Color
gray: Color
dark_gray: Color
black: Color
red: Color
yellow: Color
lime: Color
green: Color
turquoise: Color
cyan: Color
azure: Color
blue: Color
violet: Color
magenta: Color
pink: Color
brown: Color
olive: Color
peach: Color
gold: Color
salmon: Color
orange: Color
clear: Color
