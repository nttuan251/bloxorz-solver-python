import math
from collections.abc import Callable
from enum import Enum
from functools import partial
from typing import TypedDict, TypeVar

from ursina import Button, Entity, Text, camera, color, destroy
from ursina.color import Color

from src.solver_algorithms.core.cost_calculator_type import CostCalculatorType
from src.solver_algorithms.core.heuristic_calculator_type import HeuristicCalculatorType

Callback = Callable[[], None]
LevelCallback = Callable[[int], None]
SolveCallback = Callable[[str], None]

ACTIVE_LEVEL_COLOR = color.hex("#ff7f00")
INACTIVE_LEVEL_COLOR = color.hex("#222836")

_E = TypeVar("_E", bound=Enum)

Text.default_font = "assets/Montserrat-Medium.ttf"

def _next_member(current: _E) -> _E:
    members = list(type(current))
    return members[(members.index(current) + 1) % len(members)]


def _option_label(prefix: str, value: Enum) -> str:
    return f"{prefix}: {value.name.replace('_', ' ')}"


class HelpPage(TypedDict):
    title: str
    desc: str
    image: str


HELP_PAGES: list[HelpPage] = [
    {
        "title": "1. Basic Controls & Goal Hole",
        "desc": "Roll the 1x1x2 block across floor tiles using Arrow Keys.\nTo win the stage, the block MUST stand upright directly into the Goal Hole.",
        "image": "./assets/help_goal.png",
    },
    {
        "title": "2. Fragile Tiles (Red / Orange)",
        "desc": "Fragile tiles can support the block ONLY when its weight is distributed (lying horizontally or vertically).\nIf the block stands upright on a fragile tile, it breaks and falls!",
        "image": "./assets/help_fragile.png",
    },
    {
        "title": "3. Soft Switch (Circle / Octagon)",
        "desc": "Activated when ANY part of the block presses it, regardless of orientation (standing or lying).\nTriggers connected bridge tiles to toggle between open and closed states.",
        "image": "./assets/help_soft_switch.png",
    },
    {
        "title": "4. Heavy Switch (X-shaped)",
        "desc": "Activated ONLY when the block is standing upright directly on top of it.\nLying across this switch will NOT trigger it.",
        "image": "./assets/help_heavy_switch.png",
    },
    {
        "title": "5. Split Switch & Cubes (Triangle)",
        "desc": "Activated when standing upright on it. Teleports and splits the block into two 1x1x1 cubes.\nUse SPACEBAR to switch control between cubes. Cubes merge back when adjacent.\n*Note: Single cubes can press Soft Switches, but CANNOT activate Heavy Switches or win the stage.",
        "image": "./assets/help_split_switch.png",
    },
]


class HelpPanel:
    def __init__(self) -> None:
        bg_dark_color = color.rgba(10 / 255, 12 / 255, 16 / 255, 0.88)

        self.modal_bg = Button(
            parent=camera.ui,
            model="quad",
            color=bg_dark_color,
            highlight_color=bg_dark_color,
            pressed_color=bg_dark_color,
            scale=(2, 2),
            z=-10,
            enabled=False,
            on_click=self.close,
        )
        self.panel_border = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#00adb5"),
            scale=(0.85, 0.82),
            z=-10.8,
            enabled=False,
        )
        self.panel_frame = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#141822"),
            scale=(0.84, 0.81),
            z=-11,
            enabled=False,
        )
        self.panel_title = Text(
            text="[ GAMEPLAY GUIDE & MECHANICS ]",
            parent=self.panel_frame,
            position=(0, 0.43, -0.01),
            origin=(0, 0),
            scale=1.3,
            color=color.hex("#00fff5"),
        )
        self.btn_close = Button(
            text="X",
            parent=self.panel_frame,
            model="quad",
            color=color.hex("#8c2424"),
            highlight_color=color.hex("#ff4d4d"),
            scale=(0.04, 0.05),
            position=(0.45, 0.43, -0.01),
            on_click=self.close,
        )

        self.current_page = 0

        self.item_title = Text(
            text="",
            parent=self.panel_frame,
            position=(0, 0.37, -0.01),
            origin=(0, 0),
            scale=1.15,
            color=color.hex("#ff7f00"),
        )
        self.item_desc = Text(
            text="",
            parent=self.panel_frame,
            position=(0, 0.30, -0.01),
            origin=(0, 0),
            scale=0.80,
            color=color.light_gray,
            line_height=1.4,
        )
        self.img_entity = Entity(
            parent=self.panel_frame,
            model="quad",
            scale=(0.60, 0.63),
            position=(0, -0.10, -0.01),
        )
        self.btn_prev = Button(
            text="< PREV",
            parent=self.panel_frame,
            model="quad",
            color=color.hex("#1f2430"),
            highlight_color=color.hex("#00adb5"),
            scale=(0.12, 0.06),
            position=(-0.40, -0.10, -0.01),
            on_click=self.prev_page,
        )
        self.page_indicator = Text(
            text="",
            parent=self.panel_frame,
            position=(0, -0.45, -0.01),
            origin=(0, 0),
            scale=0.9,
            color=color.hex("#00fff5"),
        )
        self.btn_next = Button(
            text="NEXT >",
            parent=self.panel_frame,
            model="quad",
            color=color.hex("#1f2430"),
            highlight_color=color.hex("#00adb5"),
            scale=(0.12, 0.06),
            position=(0.40, -0.10, -0.01),
            on_click=self.next_page,
        )

        self._update_page_content()

    def _update_page_content(self) -> None:
        page = HELP_PAGES[self.current_page]
        self.item_title.text = page["title"]
        self.item_desc.text = page["desc"]
        self.img_entity.texture = page["image"]
        self.page_indicator.text = f"PAGE {self.current_page + 1} / {len(HELP_PAGES)}"

    def prev_page(self) -> None:
        self.current_page = (self.current_page - 1) % len(HELP_PAGES)
        self._update_page_content()

    def next_page(self) -> None:
        self.current_page = (self.current_page + 1) % len(HELP_PAGES)
        self._update_page_content()

    def _set_visible(self, visible: bool) -> None:
        self.modal_bg.enabled = visible
        self.panel_border.enabled = visible
        self.panel_frame.enabled = visible

    def toggle(self) -> None:
        self._set_visible(not self.modal_bg.enabled)

    def close(self) -> None:
        self._set_visible(False)


class HUD:
    def __init__(
        self,
        on_solve_click: SolveCallback,
        on_manual_click: Callback,
        on_level_change: LevelCallback,
        on_select_level: LevelCallback,
        on_restart_click: Callback,
        max_levels: int = 5,
    ) -> None:
        self.on_select_level = on_select_level
        self.max_levels = max_levels
        self.current_level = 1
        self.selected_cost = CostCalculatorType.UNIFORM
        self.selected_heuristic = HeuristicCalculatorType.TELEPORT_AWARE

        # --- DYNAMIC STATS PANEL ---
        TOP_Y = 0.474  # Mép trên của dãy nút HUD

        self.stats_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=color.rgba(20 / 255, 24 / 255, 34 / 255, 0.88),
            origin=(-0.5, 0.5),
            position=(-0.86, TOP_Y, -0.01),
            scale=(0.32, 0.09),
        )
        self.stats_border = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#00adb5"),
            origin=(-0.5, 0.5),
            position=(-0.862, TOP_Y + 0.002, -0.009),
            scale=(0.324, 0.094),
        )
        self.stats_accent = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#00fff5"),
            origin=(-0.5, 0.5),
            position=(-0.86, TOP_Y, -0.015),
            scale=(0.006, 0.09),
        )
        self.stats_text = Text(
            text="[MANUAL] Ready",
            parent=camera.ui,
            position=(-0.84, TOP_Y - 0.012, -0.02),
            origin=(-0.5, 0.5),
            scale=0.75,
            color=color.hex("#8BE9E2"),
            line_height=1.2,
        )

        self.btn_prev = self._create_cad_button(
            text="‹", color_bg=color.hex("#1f2430"), scale=(0.045, 0.038),
            pos=(-0.30, 0.455), on_click=partial(on_level_change, -1),
        )
        self.btn_level_menu = self._create_cad_button(
            text="LV 01", color_bg=color.hex("#00adb5"), scale=(0.09, 0.038),
            pos=(-0.22, 0.455), accent_color=color.hex("#00fff5"),
            on_click=self.toggle_level_panel,
        )
        self.btn_next = self._create_cad_button(
            text="›", color_bg=color.hex("#1f2430"), scale=(0.045, 0.038),
            pos=(-0.14, 0.455), on_click=partial(on_level_change, 1),
        )

        self.btn_bfs = self._create_cad_button(
            text="BFS", color_bg=color.hex("#1a2638"), scale=(0.065, 0.038),
            pos=(-0.045, 0.455), accent_color=color.azure,
            on_click=partial(on_solve_click, "bfs"),
        )
        self.btn_dfs = self._create_cad_button(
            text="DFS", color_bg=color.hex("#38281a"), scale=(0.065, 0.038),
            pos=(0.03, 0.455), accent_color=color.orange,
            on_click=partial(on_solve_click, "dfs"),
        )
        self.btn_ucs = self._create_cad_button(
            text="UCS", color_bg=color.hex("#1a3838"), scale=(0.065, 0.038),
            pos=(0.105, 0.455), accent_color=color.cyan,
            on_click=partial(on_solve_click, "ucs"),
        )
        self.btn_astar = self._create_cad_button(
            text="A*", color_bg=color.hex("#22381a"), scale=(0.065, 0.038),
            pos=(0.18, 0.455), accent_color=color.lime,
            on_click=partial(on_solve_click, "astar"),
        )
        self.btn_manual = self._create_cad_button(
            text="MANUAL", color_bg=color.hex("#381a1a"), scale=(0.14, 0.038),
            pos=(0.355, 0.455), accent_color=color.red, on_click=on_manual_click,
        )
        self.btn_restart = self._create_cad_button(
            text="RESET", color_bg=color.hex("#38281a"), scale=(0.09, 0.038),
            pos=(0.48, 0.455), accent_color=color.orange, on_click=on_restart_click,
        )

        self.help_panel = HelpPanel()
        self.btn_help = self._create_cad_button(
            text="HELP", color_bg=color.hex("#1f2430"), scale=(0.08, 0.038),
            pos=(0.68, 0.455), accent_color=color.hex("#00fff5"),
            on_click=self.help_panel.toggle,
        )
        self.btn_settings = self._create_cad_button(
            text="SETTINGS", color_bg=color.hex("#1f2430"), scale=(0.14, 0.038),
            pos=(0.8, 0.455), accent_color=color.hex("#00adb5"),
            on_click=self.toggle_settings_panel,
        )

        bg_dark_color = color.rgba(10 / 255, 12 / 255, 16 / 255, 0.85)

        self.modal_bg = Button(
            parent=camera.ui,
            model="quad",
            radius=0,
            color=bg_dark_color,
            highlight_color=bg_dark_color,
            pressed_color=bg_dark_color,
            scale=(2, 2),
            z=-10,
            enabled=False,
            on_click=self.close_level_panel,
        )
        self.panel_border = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#00adb5"),
            scale=(0.60, 0.50),
            z=-10.8,
            enabled=False,
        )
        self.panel_frame = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#141822"),
            scale=(0.60, 0.50),
            z=-11,
            enabled=False,
        )
        self.panel_title = Text(
            text="[ STAGE SELECT ]",
            parent=self.panel_frame,
            position=(0, 0.40, -0.01),
            origin=(0, 0),
            scale=1.4,
            color=color.hex("#00fff5"),
        )
        self.btn_close = Button(
            text="X",
            parent=self.panel_frame,
            model="quad",
            radius=0,
            color=color.hex("#8c2424"),
            highlight_color=color.hex("#ff4d4d"),
            scale=(0.07, 0.07),
            position=(0.42, 0.40, -0.01),
            highlight_scale=1.05,
            on_click=self.close_level_panel,
        )

        self.level_grid_buttons: list[Button] = []
        self._build_level_grid()
        self._build_settings_panel()

    def _build_settings_panel(self) -> None:
        """Advanced solver options live in a separate modal with matching HelpPanel design."""
        bg_dark_color = color.rgba(10 / 255, 12 / 255, 16 / 255, 0.88)
        self.settings_modal_bg = Button(
            parent=camera.ui,
            model="quad",
            color=bg_dark_color,
            highlight_color=bg_dark_color,
            pressed_color=bg_dark_color,
            scale=(2, 2),
            z=-20,
            enabled=False,
            on_click=self.close_settings_panel,
        )
        self.settings_border = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#00adb5"),
            scale=(0.85, 0.82),
            z=-20.8,
            enabled=False,
        )
        self.settings_frame = Entity(
            parent=camera.ui,
            model="quad",
            color=color.hex("#141822"),
            scale=(0.84, 0.81),
            z=-21,
            enabled=False,
        )
        self.settings_title = Text(
            text="[ ADVANCED SETTINGS ]",
            parent=self.settings_frame,
            position=(0, 0.43, -0.01),
            origin=(0, 0),
            scale=1.3,
            color=color.hex("#00fff5"),
        )
        self.settings_close = Button(
            text="X",
            parent=self.settings_frame,
            model="quad",
            color=color.hex("#8c2424"),
            highlight_color=color.hex("#ff4d4d"),
            scale=(0.04, 0.05),
            position=(0.45, 0.43, -0.01),
            on_click=self.close_settings_panel,
        )
        self.btn_cost = self._create_settings_button(
            text=_option_label("COST", self.selected_cost),
            pos=(0, 0.12),
            accent=color.yellow,
            callback=self._cycle_cost,
        )
        self.btn_heuristic = self._create_settings_button(
            text=_option_label("HEURISTIC", self.selected_heuristic),
            pos=(0, -0.08),
            accent=color.violet,
            callback=self._cycle_heuristic,
        )
        self.settings_hint = Text(
            text="Select a button to cycle through available algorithms",
            parent=self.settings_frame,
            position=(0, -0.35, -0.01),
            origin=(0, 0),
            scale=0.85,
            color=color.light_gray,
        )

    def _create_settings_button(
        self,
        text: str,
        pos: tuple[float, float],
        accent: Color,
        callback: Callback,
    ) -> Button:
        btn = Button(
            text=text,
            parent=self.settings_frame,
            model="quad",
            color=color.hex("#222836"),
            highlight_color=color.hex("#00adb5"),
            pressed_color=color.hex("#18202b"),
            text_color=color.white,
            scale=(0.65, 0.12),
            position=(pos[0], pos[1], -0.01),
            on_click=callback,
        )
        Entity(
            parent=btn,
            model="quad",
            color=accent,
            scale=(0.012, 0.75),
            position=(-0.48, 0, -0.01),
        )
        return btn

    def toggle_settings_panel(self) -> None:
        visible = not self.settings_modal_bg.enabled
        self.settings_modal_bg.enabled = visible
        self.settings_border.enabled = visible
        self.settings_frame.enabled = visible
        if visible:
            self.close_level_panel()
            self.help_panel.close()

    def close_settings_panel(self) -> None:
        self.settings_modal_bg.enabled = False
        self.settings_border.enabled = False
        self.settings_frame.enabled = False

    def _create_cad_button(
        self,
        text: str,
        color_bg: Color,
        scale: tuple[float, float],
        pos: tuple[float, float],
        accent_color: Color | None = None,
        on_click: Callback | None = None,
    ) -> Button:
        btn = Button(
            text=text,
            parent=camera.ui,
            model="quad",
            color=color_bg,
            highlight_color=color_bg.tint(0.25),
            pressed_color=color_bg.tint(-0.2),
            text_color=color.white,
            scale=scale,
            position=pos,
            highlight_scale=1.04,
            pressed_scale=0.96,
            on_click=on_click,
        )
        if accent_color:
            Entity(
                parent=btn,
                model="quad",
                color=accent_color,
                scale=(0.04, 0.85),
                position=(-0.47, 0, -0.01),
            )
        return btn

    def _grid_layout(self) -> tuple[int, float, float]:
        if self.max_levels > 25:
            return 7, 0.065, 0.015
        if self.max_levels > 15:
            return 6, 0.075, 0.018
        return 5, 0.085, 0.020

    def _build_level_grid(self) -> None:
        for btn in self.level_grid_buttons:
            destroy(btn)
        self.level_grid_buttons.clear()

        cols, btn_size, spacing = self._grid_layout()
        rows = math.ceil(self.max_levels / cols)
        grid_w = cols * btn_size + (cols - 1) * spacing
        grid_h = rows * btn_size + (rows - 1) * spacing

        frame_w = max(0.55, grid_w + 0.12)
        frame_h = max(0.38, grid_h + 0.16)

        self.panel_frame.scale = (frame_w, frame_h)
        self.panel_border.scale = (frame_w + 0.008, frame_h + 0.008)

        y_top = 0.5 - (0.05 / frame_h)
        self.panel_title.position = (0, y_top, -0.01)

        close_w = 0.045 / frame_w
        close_h = 0.045 / frame_h
        self.btn_close.scale = (close_w, close_h)
        self.btn_close.position = (0.5 - close_w * 1.2, y_top, -0.01)

        step_x = (btn_size + spacing) / frame_w
        step_y = (btn_size + spacing) / frame_h
        start_x = -((cols - 1) * step_x) / 2
        start_y = y_top - (0.08 / frame_h)
        btn_w = btn_size / frame_w
        btn_h = btn_size / frame_h

        for level in range(1, self.max_levels + 1):
            row, col = divmod(level - 1, cols)
            self.level_grid_buttons.append(
                Button(
                    text=f"{level:02d}",
                    parent=self.panel_frame,
                    model="quad",
                    radius=0.03,
                    color=self._level_color(level),
                    highlight_color=color.hex("#00adb5"),
                    text_color=color.white,
                    scale=(btn_w, btn_h),
                    position=(start_x + col * step_x, start_y - row * step_y, -0.01),
                    highlight_scale=1.06,
                    pressed_scale=0.95,
                    on_click=partial(self._on_grid_level_click, level),
                )
            )

    def _cycle_cost(self) -> None:
        self.selected_cost = _next_member(self.selected_cost)
        self.btn_cost.text = _option_label("COST", self.selected_cost)

    def _cycle_heuristic(self) -> None:
        self.selected_heuristic = _next_member(self.selected_heuristic)
        self.btn_heuristic.text = _option_label("HEURISTIC", self.selected_heuristic)

    def _level_color(self, level: int) -> Color:
        return (
            ACTIVE_LEVEL_COLOR if level == self.current_level else INACTIVE_LEVEL_COLOR
        )

    def _on_grid_level_click(self, level: int) -> None:
        self.close_level_panel()
        self.on_select_level(level)

    def _set_level_panel_visible(self, visible: bool) -> None:
        self.modal_bg.enabled = visible
        self.panel_border.enabled = visible
        self.panel_frame.enabled = visible

    def toggle_level_panel(self) -> None:
        visible = not self.modal_bg.enabled
        self._set_level_panel_visible(visible)
        if visible:
            self.refresh_panel_highlight()

    def close_level_panel(self) -> None:
        self._set_level_panel_visible(False)

    def update_level_display(self, level_num: int) -> None:
        self.current_level = level_num
        self.btn_level_menu.text = f"LV {level_num:02d}"
        self.refresh_panel_highlight()

    def refresh_panel_highlight(self) -> None:
        for level, btn in enumerate(self.level_grid_buttons, start=1):
            btn.color = self._level_color(level)

    def update_stats(self, msg: str) -> None:
        self.stats_text.text = msg
        lines = msg.split("\n")
        num_lines = len(lines)

        # 1. Tính chiều rộng dựa trên dòng chữ dài nhất
        max_chars = max(len(line) for line in lines) if lines else 0
        # Cỡ chữ scale=0.60: mỗi ký tự chiếm khoảng ~0.0105 độ rộng màn hình
        new_w = max(0.32, (max_chars * 0.0105) + 0.04)

        # 2. Tính chiều cao dựa trên số lượng dòng (khoảng cách thực tế ~0.020/dòng)
        new_h = 0.025 + (num_lines * 0.022)

        # 3. Cập nhật kích thước đồng bộ cho Panel, Border và Accent line
        self.stats_panel.scale = (new_w, new_h)
        self.stats_border.scale = (new_w + 0.004, new_h + 0.004)
        self.stats_accent.scale = (0.006, new_h)
