# src/gui/ui.py
import math
from ursina import Entity, Button, Text, camera, color, destroy


class HelpPanel:
    """Bảng Hướng Dẫn phân trang (Carousel) hiển thị hình ảnh minh họa và mô tả cơ chế game."""

    def __init__(self):
        bg_dark_color = color.rgba(10 / 255, 12 / 255, 16 / 255, 0.88)

        self.modal_bg = Button(
            parent=camera.ui,
            model='quad',
            color=bg_dark_color,
            highlight_color=bg_dark_color,
            pressed_color=bg_dark_color,
            scale=(2, 2),
            z=-10,
            enabled=False,
            on_click=self.close
        )

        self.panel_border = Entity(
            parent=camera.ui,
            model='quad',
            color=color.hex('#00adb5'),
            scale=(0.85, 0.82),
            z=-10.8,
            enabled=False
        )
        self.panel_frame = Entity(
            parent=camera.ui,
            model='quad',
            color=color.hex('#141822'),
            scale=(0.84, 0.81),
            z=-11,
            enabled=False
        )

        self.panel_title = Text(
            text="[ GAMEPLAY GUIDE & MECHANICS ]",
            parent=self.panel_frame,
            position=(0, 0.43, -0.01),
            origin=(0, 0),
            scale=1.3,
            color=color.hex('#00fff5')
        )

        self.btn_close = Button(
            text="X",
            parent=self.panel_frame,
            model='quad',
            color=color.hex('#8c2424'),
            highlight_color=color.hex('#ff4d4d'),
            scale=(0.04, 0.05),
            position=(0.45, 0.43, -0.01),
            on_click=self.close
        )

        self.pages = [
            {
                "title": "1. Basic Controls & Goal Hole",
                "desc": "Roll the 1x1x2 block across floor tiles using Arrow Keys.\nTo win the stage, the block MUST stand upright directly into the Goal Hole.",
                "image": "./assets/help_goal.png"
            },
            {
                "title": "2. Fragile Tiles (Red / Orange)",
                "desc": "Fragile tiles can support the block ONLY when its weight is distributed (lying horizontally or vertically).\nIf the block stands upright on a fragile tile, it breaks and falls!",
                "image": "./assets/help_fragile.png"
            },
            {
                "title": "3. Soft Switch (Circle / Octagon)",
                "desc": "Activated when ANY part of the block presses it, regardless of orientation (standing or lying).\nTriggers connected bridge tiles to toggle between open and closed states.",
                "image": "./assets/help_soft_switch.png"
            },
            {
                "title": "4. Heavy Switch (X-shaped)",
                "desc": "Activated ONLY when the block is standing upright directly on top of it.\nLying across this switch will NOT trigger it.",
                "image": "./assets/help_heavy_switch.png"
            },
            {
                "title": "5. Split Switch & Cubes (Triangle)",
                "desc": "Activated when standing upright on it. Teleports and splits the block into two 1x1x1 cubes.\nUse SPACEBAR to switch control between cubes. Cubes merge back when adjacent.\n*Note: Single cubes can press Soft Switches, but CANNOT activate Heavy Switches or win the stage.",
                "image": "./assets/help_split_switch.png"
            }
        ]

        self.current_page = 0

        self.item_title = Text(
            text="",
            parent=self.panel_frame,
            position=(0, 0.37, -0.01),
            origin=(0, 0),
            scale=1.15,
            color=color.hex('#ff7f00')
        )
        self.item_desc = Text(
            text="",
            parent=self.panel_frame,
            position=(0, 0.30, -0.01),
            origin=(0, 0),
            scale=0.80,
            color=color.light_gray,
            line_height=1.4
        )

        self.img_entity = Entity(
            parent=self.panel_frame,
            model='quad',
            scale=(0.60, 0.63),
            position=(0, -0.10, -0.01)
        )

        self.btn_prev = Button(
            text="< PREV",
            parent=self.panel_frame,
            model='quad',
            color=color.hex('#1f2430'),
            highlight_color=color.hex('#00adb5'),
            scale=(0.12, 0.06),
            position=(-0.40, -0.10, -0.01),
            on_click=self.prev_page
        )

        self.page_indicator = Text(
            text="",
            parent=self.panel_frame,
            position=(0, -0.45, -0.01),
            origin=(0, 0),
            scale=0.9,
            color=color.hex('#00fff5')
        )

        self.btn_next = Button(
            text="NEXT >",
            parent=self.panel_frame,
            model='quad',
            color=color.hex('#1f2430'),
            highlight_color=color.hex('#00adb5'),
            scale=(0.12, 0.06),
            position=(0.40, -0.10, -0.01),
            on_click=self.next_page
        )

        self._update_page_content()

    def _update_page_content(self):
        """Cập nhật văn bản, hình ảnh minh họa và chỉ số trang hiện tại."""
        data = self.pages[self.current_page]
        self.item_title.text = data["title"]
        self.item_desc.text = data["desc"]
        self.img_entity.texture = data["image"]
        self.page_indicator.text = f"PAGE {self.current_page + 1} / {len(self.pages)}"

    def prev_page(self):
        """Chuyển về trang hướng dẫn trước đó."""
        self.current_page = (self.current_page - 1) % len(self.pages)
        self._update_page_content()

    def next_page(self):
        """Chuyển sang trang hướng dẫn tiếp theo."""
        self.current_page = (self.current_page + 1) % len(self.pages)
        self._update_page_content()

    def toggle(self):
        """Bật hoặc tắt hiển thị Bảng Hướng Dẫn."""
        is_open = not self.modal_bg.enabled
        self.modal_bg.enabled = is_open
        self.panel_border.enabled = is_open
        self.panel_frame.enabled = is_open

    def close(self):
        """Ẩn Bảng Hướng Dẫn."""
        self.modal_bg.enabled = False
        self.panel_border.enabled = False
        self.panel_frame.enabled = False


class HUD:
    """Quản lý các thành phần giao diện người dùng 2D (thông số, nút điều khiển, menu chọn màn)."""

    def __init__(self, on_solve_click, on_manual_click, on_level_change, on_select_level, on_restart_click, max_levels=5):
        self.on_select_level = on_select_level
        self.max_levels = max_levels
        self.current_level = 1

        self.stats_text = Text(
            text="[MANUAL MODE] Ready",
            position=(-0.85, 0.45),
            scale=1.0,
            color=color.yellow,
            line_height=1.35
        )

        # Thanh điều hướng màn chơi & chức năng
        self.btn_prev = self._create_cad_button(text='PREV', color_bg=color.hex('#1f2430'), scale=(0.07, 0.04), pos=(0.20, 0.45), on_click=lambda: on_level_change(-1))
        self.btn_level_menu = self._create_cad_button(text="LV 01", color_bg=color.hex('#00adb5'), scale=(0.09, 0.04), pos=(0.29, 0.45), accent_color=color.hex('#00fff5'), on_click=self.toggle_level_panel)
        self.btn_next = self._create_cad_button(text='NEXT', color_bg=color.hex('#1f2430'), scale=(0.07, 0.04), pos=(0.38, 0.45), on_click=lambda: on_level_change(1))
        self.btn_restart = self._create_cad_button(text='RESTART', color_bg=color.hex('#38281a'), scale=(0.12, 0.04), pos=(0.55, 0.45), accent_color=color.orange, on_click=on_restart_click)

        # Các nút kích hoạt thuật toán tìm kiếm AI
        self.btn_bfs = self._create_cad_button(text='BFS', color_bg=color.hex('#1a2638'), scale=(0.07, 0.04), pos=(0.20, 0.39), accent_color=color.azure, on_click=lambda: on_solve_click('bfs'))
        self.btn_dfs = self._create_cad_button(text='DFS', color_bg=color.hex('#38281a'), scale=(0.07, 0.04), pos=(0.28, 0.39), accent_color=color.orange, on_click=lambda: on_solve_click('dfs'))
        self.btn_ucs = self._create_cad_button(text='UCS', color_bg=color.hex('#1a3838'), scale=(0.07, 0.04), pos=(0.36, 0.39), accent_color=color.cyan, on_click=lambda: on_solve_click('ucs'))
        self.btn_astar = self._create_cad_button(text='A*', color_bg=color.hex('#22381a'), scale=(0.07, 0.04), pos=(0.44, 0.39), accent_color=color.lime, on_click=lambda: on_solve_click('astar'))
        self.btn_manual = self._create_cad_button(text='MANUAL', color_bg=color.hex('#381a1a'), scale=(0.12, 0.04), pos=(0.55, 0.39), accent_color=color.red, on_click=on_manual_click)

        self.help_panel = HelpPanel()

        self.btn_help = self._create_cad_button(
            text='HELP',
            color_bg=color.hex('#1f2430'),
            scale=(0.07, 0.04),
            pos=(0.66, 0.45),
            accent_color=color.hex('#00fff5'),
            on_click=self.help_panel.toggle
        )

        # Popup chọn màn chơi (Stage Select Modal)
        bg_dark_color = color.rgba(10 / 255, 12 / 255, 16 / 255, 0.85)

        self.modal_bg = Button(
            parent=camera.ui,
            model='quad',
            radius=0,
            color=bg_dark_color,
            highlight_color=bg_dark_color,
            pressed_color=bg_dark_color,
            scale=(2, 2),
            z=-10,
            enabled=False,
            on_click=self.close_level_panel
        )

        self.panel_border = Entity(parent=camera.ui, model='quad', color=color.hex('#00adb5'), scale=(0.60, 0.50), z=-10.8, enabled=False)
        self.panel_frame = Entity(parent=camera.ui, model='quad', color=color.hex('#141822'), scale=(0.60, 0.50), z=-11, enabled=False)
        self.panel_title = Text(text="[ STAGE SELECT ]", parent=self.panel_frame, position=(0, 0.40, -0.01), origin=(0, 0), scale=1.4, color=color.hex('#00fff5'))

        self.btn_close = Button(
            text="X",
            parent=self.panel_frame,
            model='quad',
            radius=0,
            color=color.hex('#8c2424'),
            highlight_color=color.hex('#ff4d4d'),
            scale=(0.07, 0.07),
            position=(0.42, 0.40, -0.01),
            highlight_scale=1.05,
            on_click=self.close_level_panel
        )

        self.level_grid_buttons = []
        self._build_level_grid()

    def _create_cad_button(self, text, color_bg, scale, pos, accent_color=None, on_click=None):
        """Tạo nút bấm chuẩn phong cách CAD kèm dải màu accent bên hông."""
        btn = Button(
            text=text,
            parent=camera.ui,
            model='quad',
            color=color_bg,
            highlight_color=color_bg.tint(0.25),
            pressed_color=color_bg.tint(-0.2),
            text_color=color.white,
            scale=scale,
            position=pos,
            highlight_scale=1.04,
            pressed_scale=0.96,
            on_click=on_click
        )
        if accent_color:
            Entity(
                parent=btn,
                model='quad',
                color=accent_color,
                scale=(0.04, 0.85),
                position=(-0.47, 0, -0.01)
            )
        return btn

    def _build_level_grid(self):
        """Khởi tạo lưới danh sách các nút chọn màn chơi tự động căn chỉnh."""
        for btn in self.level_grid_buttons:
            destroy(btn)
        self.level_grid_buttons.clear()

        if self.max_levels > 25:
            cols, btn_size, spacing = 7, 0.065, 0.015
        elif self.max_levels > 15:
            cols, btn_size, spacing = 6, 0.075, 0.018
        else:
            cols, btn_size, spacing = 5, 0.085, 0.020

        rows = math.ceil(self.max_levels / cols)
        grid_w_world = cols * btn_size + (cols - 1) * spacing
        grid_h_world = rows * btn_size + (rows - 1) * spacing

        frame_w = max(0.55, grid_w_world + 0.12)
        frame_h = max(0.38, grid_h_world + 0.16)

        self.panel_frame.scale = (frame_w, frame_h)
        self.panel_border.scale = (frame_w + 0.008, frame_h + 0.008)

        y_top_local = 0.5 - (0.05 / frame_h)
        self.panel_title.position = (0, y_top_local, -0.01)

        close_w_local = 0.045 / frame_w
        close_h_local = 0.045 / frame_h
        self.btn_close.scale = (close_w_local, close_h_local)
        self.btn_close.position = (0.5 - close_w_local * 1.2, y_top_local, -0.01)

        step_x = (btn_size + spacing) / frame_w
        step_y = (btn_size + spacing) / frame_h

        start_x = -((cols - 1) * step_x) / 2
        start_y = y_top_local - (0.08 / frame_h)

        btn_w_local = btn_size / frame_w
        btn_h_local = btn_size / frame_h

        for i in range(1, self.max_levels + 1):
            r = (i - 1) // cols
            c = (i - 1) % cols

            x_pos = start_x + c * step_x
            y_pos = start_y - r * step_y

            is_active = (i == self.current_level)
            btn_color = color.hex('#ff7f00') if is_active else color.hex('#222836')

            btn = Button(
                text=f"{i:02d}",
                parent=self.panel_frame,
                model='quad',
                radius=0.03,
                color=btn_color,
                highlight_color=color.hex('#00adb5'),
                text_color=color.white,
                scale=(btn_w_local, btn_h_local),
                position=(x_pos, y_pos, -0.01),
                highlight_scale=1.06,
                pressed_scale=0.95
            )
            btn.on_click = lambda lvl=i: self._on_grid_level_click(lvl)
            self.level_grid_buttons.append(btn)

    def _on_grid_level_click(self, lvl_num):
        """Xử lý khi nhấp chọn một màn chơi trong bảng lưới."""
        self.close_level_panel()
        if self.on_select_level:
            self.on_select_level(lvl_num)

    def toggle_level_panel(self):
        """Đóng hoặc mở bảng danh sách chọn màn chơi."""
        is_open = not self.modal_bg.enabled
        self.modal_bg.enabled = is_open
        self.panel_border.enabled = is_open
        self.panel_frame.enabled = is_open
        if is_open:
            self.refresh_panel_highlight()

    def close_level_panel(self):
        """Ẩn bảng chọn màn chơi."""
        self.modal_bg.enabled = False
        self.panel_border.enabled = False
        self.panel_frame.enabled = False

    def update_level_display(self, level_num):
        """Cập nhật số hiệu màn chơi hiển thị trên nút menu."""
        self.current_level = level_num
        self.btn_level_menu.text = f"LV {level_num:02d}"
        self.refresh_panel_highlight()

    def refresh_panel_highlight(self):
        """Cập nhật màu highlight cho nút đại diện cho màn chơi hiện tại."""
        for idx, btn in enumerate(self.level_grid_buttons, start=1):
            btn.color = color.hex('#ff7f00') if idx == self.current_level else color.hex('#222836')

    def update_stats(self, msg):
        """Cập nhật thông tin chỉ số / trạng thái trên HUD."""
        self.stats_text.text = msg