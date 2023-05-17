import json
import jsonschema
import math
import os
import pygame
import pygame_widgets as pygamew
from sys import exit
from pygame import gfxdraw
from enum import Enum, auto
from match3_board import Match3Board


class GameState(Enum):
    MAINMENU = auto()
    CHOOSESIZE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ENDED = auto()
    ENTERHIGHSCORE = auto()
    HIGHSCORES = auto()
    PREFERENCES = auto()
    ABOUT = auto()


class MouseState(Enum):
    WAITING = auto()
    PRESSED = auto()
    MOVING = auto()


class Match3GUI:
    colors = (
        (  0,  0,128),  # 000080 Dark Blue
        (128,  0,  0),  # 800000 Dark Red
        (  0,128,  0),  # 008000 Green
        (255,255,  0),  # FFFF00 Yellow
        (255,255,255),  # FFFFFF White
        (  0,  0,  0),  # 000000 Black
        ( 84, 84, 84),  # 545454 Grey
        (192,  0,192),  # C000C0 Purple-Magenta
        (172,172,255),  # ACACFF Light Blue
        (255, 64, 64),  # FF4040 Light Red
        (192,255,128),  # C0FF80 Pale Green-Yellow
        ( 48,192,192),  # 30C0C0 Greyed Cyan
    )
    border_color = (48, 48, 48)
    background_color = {
        "screen": (0, 0, 0),
        "game": (24, 24, 24),
        "board": (0, 0, 0),
        "sidebar": (48, 48, 48),
    }
    hint_color = (255, 255, 255)
    widget_text_color = (255, 255, 255)
    starting_width = 640
    starting_height = 480
    game_ratio = starting_width / starting_height
    board_scale = 9 / 10
    circle_scale = 18 / 20
    plus_score_ani_time = 500
    hint_ani_time = 500
    swap_ani_time = 200
    shift_down_ani_time = 200
    clear_ani_time = 200
    plus_score_blink_ani_time = 100
    ani_fps = 60
    main_loop_refresh_rate = 30
    flags = pygame.RESIZABLE | pygame.HWSURFACE
    min_font_size = 20
    min_char_width = 13.8
    min_char_height = 13.8
    min_char_sep_height = min_char_height / 2
    time_init = 60000
    board_sizes = list(range(5, 14))
    high_score_name_max_len = 20
    high_scores_filename = "high_scores.json"
    high_scores_schema = '''
    {
        "type": "object",
        "additionalProperties": {
            "type": "array",
            "items": {
                "type": "array",
                "items": [
                    {"type": "string", "maxLength": 20},
                    {"type": "integer", "minimum": 1}
                ],
                "additionalProperties": false
            },
            "maxItems": 5
        },
        "propertyNames": {"enum": []}
    }
    '''
    high_scores_schema = json.loads(high_scores_schema)
    high_scores_schema["propertyNames"]["enum"] = [f"{n}x{n}" for n in board_sizes]
    preferences_filename = "preferences.json"
    preferences_schema = '''
    {
        "type": "object",
        "properties": {
            "background_music": {
                "type": "boolean"
            },
            "sound_effects": {
                "type": "boolean"
            }
        },
        "additionalProperties": false
    }
    '''
    preferences_schema = json.loads(preferences_schema)
    media_dir = "media"
    audio_dir = f"{media_dir}/audio"
    sounds_dir = f"{audio_dir}/sounds"
    music_dir = f"{audio_dir}/music"
    background_music_filename = f"{music_dir}/background_music.ogg"

    def __init__(self) -> None:
        self.board = None
        self.screen_surf = None
        self.game_surf = None
        self.board_surf = None
        self.sidebar_surf = None
        self.clock = None
        self.circle_radius = 0
        self.mouse_state = MouseState.WAITING
        self.board_pos_src = None
        self.score = 0
        self.time_left = self.time_init
        self.time_start = 0
        self.time_score = 0
        self.time_left_sec = int(self.time_left / 1000)
        self.active_widgets = {}
        self.hint = False
        self.hint_cut_score = False
        self.plus_score_ani_time_start = 0
        self.curr_plus_score_ani_time = self.plus_score_ani_time + 1
        self.curr_score = 0
        self.curr_time_score = 0
        self.game_state = GameState.MAINMENU
        self.font_size = self.min_font_size
        self.char_width = self.min_char_width
        self.char_height = self.min_char_height
        self.char_sep_height = self.min_char_sep_height
        self.font = None
        self.pause = False
        self.pause_time = 0
        self.time_paused = 0
        self.game_ended = False
        self.prev_state = None
        self.high_scores_state = 5
        self.high_scores = {}
        self.preferences = {}
        self.sounds = {}
        self.last_beep_sound_time = 0

    ##################################################
    # Animate functions
    ##################################################

    def animate_swap(self, board_point1: tuple[int, int], board_point2: tuple[int, int]) -> None:
        self.play_sound("swap")

        board_points = (board_point1, board_point2)
        win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))

        target_dist = (
            [win_points[1][0] - win_points[0][0], win_points[1][1] - win_points[0][1]],  # [dst_p1_x - src_p1_x, dst_p1_y - src_p1_y]
            [win_points[0][0] - win_points[1][0], win_points[0][1] - win_points[1][1]],  # [dst_p2_x - src_p2_x, dst_p2_y - src_p2_y]
        )
        curr_pos = [list(win_points[0]), list(win_points[1])]

        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while curr_pos[0] != win_points[1] or curr_pos[1] != win_points[0]:  # curr_p1 != dst_p1 or curr_p2 != dst_p2
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))
                target_dist = (
                    [win_points[1][0] - win_points[0][0], win_points[1][1] - win_points[0][1]],  # [dst_p1_x - src_p1_x, dst_p1_y - src_p1_y]
                    [win_points[0][0] - win_points[1][0], win_points[0][1] - win_points[1][1]],  # [dst_p2_x - src_p2_x, dst_p2_y - src_p2_y]
                )

            self.draw_board(no_draw_pts=board_points)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            for p_i in reversed(range(2)):
                # Calculate the new position
                src_pos = win_points[p_i]
                dst_pos = win_points[int(not p_i)]
                curr_dist = (target_dist[p_i][0] * curr_ani_time / self.swap_ani_time, target_dist[p_i][1] * curr_ani_time / self.swap_ani_time)
                curr_pos[p_i] = [src_pos[0] + curr_dist[0], src_pos[1] + curr_dist[1]]
                curr_pos[p_i] = [int(curr_pos[p_i][0]), int(curr_pos[p_i][1])]
                for i in range(2):
                    dir = dst_pos[i] - src_pos[i]
                    if (dir < 0 and curr_pos[p_i][i] < dst_pos[i]) or (dir > 0 and curr_pos[p_i][i] > dst_pos[i]):
                        curr_pos[p_i][i] = dst_pos[i]
                # Draw the moving circles
                color_index = self.board.board[board_points[p_i][1]][board_points[p_i][0]]
                if color_index < 0:
                    continue
                self.draw_circle(curr_pos[p_i][0], curr_pos[p_i][1], self.colors[color_index])

            pygame.display.flip()

    def animate_clear(self, board_points: list[tuple[int, int]], no_more_moves: bool = False) -> None:
        self.play_sound("match")

        win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

        target_transparency = 0
        target_size = 0
        curr_transparency = 255
        curr_size = self.circle_radius

        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        clear_ani_time = self.clear_ani_time
        if no_more_moves:
            clear_ani_time *= 5

        while curr_transparency != target_transparency or curr_size != target_size:
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

            self.draw_board(no_draw_pts=board_points)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            # Calculate the new size and the new transparency
            curr_transparency = int(target_transparency * (1 - curr_ani_time / clear_ani_time))
            if curr_transparency > target_transparency:
                curr_transparency = target_transparency
            curr_size = int(self.circle_radius * (1 - curr_ani_time / clear_ani_time))
            if curr_size < target_size:
                curr_size = target_size

            # Draw the moving circles
            for i, p in enumerate(board_points):
                color_index = self.board.board[p[1]][p[0]]
                if color_index < 0:
                    continue
                self.draw_circle(win_points[i][0], win_points[i][1], self.colors[color_index], curr_size)

            if no_more_moves:
                texts = ("NO MORE MOVES", "REGENERATING BOARD")
                width = (max([len(text) for text in texts]) + 4) * self.char_width
                height = (math.ceil(self.char_height) + math.ceil(self.char_sep_height)) * 2
                x = (self.board_surf.get_width() - width) / 2 + self.board_surf.get_abs_offset()[0]
                y = (self.board_surf.get_height() - height * 2) / 2 + self.board_surf.get_abs_offset()[1]
                for text in texts:
                    button = pygamew.Button(
                        self.screen_surf, x, y, width, height,
                        text=text,
                        textColour=(32, 255, 32),
                        font=self.font,
                        colour=self.background_color["game"],
                        hoverColour=self.background_color["game"],
                        pressedColour=self.background_color["game"]
                    )
                    button.draw()
                    y += height

            pygame.display.flip()

    def animate_shift_down(self, shifted_bp: list[tuple[int, int]], num_vertical_points: int) -> None:
        board_points_dst = shifted_bp
        board_points_src = [(x, y - 1) for (x, y) in board_points_dst]
        win_points_dst = [list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
        win_points_src = [list(self.board_pos_to_win_pos(*p)) for p in board_points_src]
        color_indices = [self.board.board[y][x] for (x, y) in board_points_dst]

        curr_pos = [[x, y] for (x, y) in win_points_src]

        ani_time = self.shift_down_ani_time / min((num_vertical_points, 2))
        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while any([curr_pos[i] != win_points_dst[i] for i in range(len(curr_pos))]):
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points_dst = [list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
                win_points_src = [list(self.board_pos_to_win_pos(*p)) for p in board_points_src]

            self.draw_board(no_draw_pts=board_points_src + board_points_dst)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            for p_i in range(len(curr_pos)):
                # Calculate the new position
                src_pos = win_points_src[p_i]
                dst_pos = win_points_dst[p_i]
                target_dist = ((dst_pos[0] - src_pos[0]), (dst_pos[1] - src_pos[1]))
                curr_dist = (target_dist[0] * curr_ani_time / ani_time, target_dist[1] * curr_ani_time / ani_time)
                curr_pos[p_i] = [src_pos[0] + curr_dist[0], src_pos[1] + curr_dist[1]]
                curr_pos[p_i] = [int(curr_pos[p_i][0]), int(curr_pos[p_i][1])]
                for i in range(2):
                    dir = dst_pos[i] - src_pos[i]
                    if (dir < 0 and curr_pos[p_i][i] < dst_pos[i]) or (dir > 0 and curr_pos[p_i][i] > dst_pos[i]):
                        curr_pos[p_i][i] = dst_pos[i]
                # Draw the moving circles
                color_index = color_indices[p_i]
                if color_index < 0:
                    continue
                self.draw_circle(curr_pos[p_i][0], curr_pos[p_i][1], self.colors[color_index])

            pygame.display.flip()

    def animate_hint(self, board_point1: tuple[int, int], board_point2: tuple[int, int]) -> None:
        self.play_sound("hint")

        board_points = (board_point1, board_point2)
        win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))

        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while curr_ani_time <= self.hint_ani_time:
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))

            self.draw_board(no_draw_pts=board_points)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            for p_i in range(2):
                color_index = self.board.board[board_points[p_i][1]][board_points[p_i][0]]
                if color_index < 0:
                    continue
                self.draw_circle(*win_points[p_i], self.hint_color, self.circle_radius / self.circle_scale)
                self.draw_circle(*win_points[p_i], self.colors[color_index])

            pygame.display.flip()

        self.update_board()

    def animate_plus_score_prev(self) -> None:
        self.curr_plus_score_ani_time = self.plus_score_ani_time + 1
        self.update_sidebar()
        pygame.time.wait(self.plus_score_blink_ani_time)

    def animate_plus_score_post(self) -> None:
        self.curr_plus_score_ani_time = 0
        self.plus_score_ani_time_start = pygame.time.get_ticks()
        self.update_sidebar()

    ##################################################
    # Draw functions
    ##################################################

    def draw_circle(self, x, y, color, radius = None) -> None:
        if radius is None:
            radius = self.circle_radius
        if color != (0, 0, 0):
            gfxdraw.aacircle(self.board_surf, x, y, int(radius * self.circle_scale), color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius * self.circle_scale), color)
        else:
            gfxdraw.aacircle(self.board_surf, x, y, int(radius * self.circle_scale), self.border_color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius * self.circle_scale), self.border_color)
            gfxdraw.aacircle(self.board_surf, x, y, int(radius * (1 - (1 - self.circle_scale) * 2)), color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius * (1 - (1 - self.circle_scale) * 2)), color)

    def draw_board(self, no_draw_pts: list[tuple[int, int]] = None) -> None:
        self.board_surf.fill(self.background_color["board"])

        for row in range(self.board.rows):
            for col in range(self.board.cols):
                if no_draw_pts is not None and (col, row) in no_draw_pts:
                    continue
                color_index = self.board.board[row][col]
                if color_index < 0:
                    continue
                pos = self.board_pos_to_win_pos(col, row)
                self.draw_circle(pos[0], pos[1], self.colors[color_index])

    def draw_buttons(self, texts, y, y_separation, surface_name) -> None:
        surface = getattr(self, f"{surface_name}_surf")
        height = (self.char_height + self.char_sep_height) * 2
        for text in texts:
            width = (len(text) + 4) * self.char_width
            x = (surface.get_width() - width) / 2 + surface.get_abs_offset()[0]
            y_abs = y + surface.get_abs_offset()[1]
            border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
            if border_thickness < 1:
                border_thickness = 1
            button_name = text.lower()
            button_name = button_name.replace(' ', '_')
            if button_name not in self.active_widgets:
                button = pygamew.Button(
                    self.screen_surf, x, y_abs, width, height,
                    text=text,
                    textColour=self.widget_text_color,
                    font=self.font,
                    colour=(64, 64, 64),
                    hoverColour=(96, 96, 96),
                    pressedColour=(128, 128, 128),
                    borderColour=(0, 0, 0),
                    hoverBorderColour=(32, 32, 32),
                    pressedBorderColour=(64, 64, 64),
                    shadowColour=[val * 2 / 3 for val in self.background_color[surface_name]],
                    shadowDistance=self.char_sep_height // 2,
                    borderThickness=border_thickness,
                    onRelease=getattr(self, f"{button_name}_clicked")
                )
                self.active_widgets[button_name] = button
            self.active_widgets[button_name].draw()
            y += height + (self.char_height + self.char_sep_height) * y_separation

    def draw_sidebar(self) -> None:
        self.sidebar_surf.fill(self.background_color["sidebar"])

        y = (self.sidebar_surf.get_height() - (self.char_height + self.char_sep_height) * 13) / 2
        for i, text in enumerate(("SCORE", str(self.score), "TIME LEFT", str(self.time_left_sec))):
            if i == 2:
                y += self.char_height + self.char_sep_height
            if i == 3:
                tc = list(self.widget_text_color)
                gb = 255 * self.time_left_sec / (self.time_init / 1000)
                if gb > 255:
                    gb = 255
                elif gb < 0:
                    gb = 0
                tc[1] = gb
                tc[2] = gb
                label = self.font.render(text, True, tc)
            else:
                label = self.font.render(text, True, self.widget_text_color)
            width = len(text) * self.char_width
            x = (self.sidebar_surf.get_width() - width) / 2
            self.sidebar_surf.blit(label, (x, y))
            if self.curr_plus_score_ani_time <= self.plus_score_ani_time:
                if i == 1 or i == 3:
                    label = self.font.render("+" + str({1: self.curr_score, 3: self.curr_time_score / 1000}.get(i)), True, (255, 255, 0))
                    x += width
                    self.sidebar_surf.blit(label, (x, y))
                self.curr_plus_score_ani_time = pygame.time.get_ticks() - self.plus_score_ani_time_start
            y += self.char_height + self.char_sep_height

        y += (self.char_height + self.char_sep_height) * 3

        texts = ("PAUSE", "HINT")
        self.draw_buttons(texts, y, 1, "sidebar")

    def draw_main_menu(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        texts = ["NEW GAME", "HIGH SCORES", "PREFERENCES", "ABOUT", "EXIT"]
        if self.game_state == GameState.PAUSED:
            texts = ["RESUME GAME"] + texts
        y = (self.game_surf.get_height() - len(texts) * (self.char_height + self.char_sep_height) * 3.5 + (self.char_height + self.char_sep_height) * 1.5) / 2
        self.draw_buttons(texts, y, 1.5, "game")

    def draw_choosesize(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 2) / 2
        texts = ("START",)
        self.draw_buttons(texts, y, 0, "game")

        y = (self.game_surf.get_height() - (len(self.board_sizes) + 1) * (self.char_height + self.char_sep_height) * 2) / 2
        text = "Choose Board Size"
        height = (self.char_height + self.char_sep_height) * 2
        width = (len(text) + 4) * self.char_width
        x = (self.game_surf.get_width() - width) / 2 + self.game_surf.get_abs_offset()[0]
        y_abs = y + self.game_surf.get_abs_offset()[1]
        border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
        if border_thickness < 1:
            border_thickness = 1
        dropdown_name = text.lower()
        dropdown_name = dropdown_name.replace(' ', '_')
        if dropdown_name not in self.active_widgets:
            dropdown = pygamew.Dropdown(
                self.screen_surf, x, y_abs, width, height,
                name=text,
                textColour=self.widget_text_color,
                font=self.font,
                inactiveColour=(64, 64, 64),
                hoverColour=(96, 96, 96),
                pressedColour=(128, 128, 128),
                borderColour=(0, 0, 0),
                hoverBorderColour=(32, 32, 32),
                pressedBorderColour=(64, 64, 64),
                borderThickness=border_thickness,
                choices=[f"{n}x{n}" for n in self.board_sizes],
                values=self.board_sizes
            )
            self.active_widgets[dropdown_name] = dropdown
        # FIXME: When window is resized dropdown is regenerated and loses its current selection.
        self.active_widgets[dropdown_name].draw()

    def draw_ended(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 9) / 2
        for i, text in enumerate(("TIME'S UP!", "YOUR SCORE:", str(self.score))):
            width = len(text) * self.char_width
            x = (self.game_surf.get_width() - width) / 2
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height)
            if i == 0:
                y += (self.char_height + self.char_sep_height) * 2

        y += (self.char_height + self.char_sep_height) * 2

        texts = ("CONTINUE",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_enterhighscore(self ) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 11) / 2
        text = "HIGH SCORE ACHIEVED!"
        width = len(text) * self.char_width
        x = (self.game_surf.get_width() - width) / 2
        label = self.font.render(text, True, self.widget_text_color)
        self.game_surf.blit(label, (x, y))

        y += (self.char_height + self.char_sep_height) * 3

        text = "Enter your name:"
        width = len(text) * self.char_width
        x = (self.game_surf.get_width() - width) / 2
        label = self.font.render(text, True, self.widget_text_color)
        self.game_surf.blit(label, (x, y))

        y += (self.char_height + self.char_sep_height) * 2

        width = (self.high_score_name_max_len + 1) * self.char_width
        height = (self.char_height + self.char_sep_height) * 2
        x = (self.game_surf.get_width() - width) / 2 + self.game_surf.get_abs_offset()[0]
        y_abs = y + self.game_surf.get_abs_offset()[1]
        border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
        if border_thickness < 1:
            border_thickness = 1
        textbox_name = "high_score_name"
        if textbox_name not in self.active_widgets:
            textbox = pygamew.TextBox(
                self.screen_surf, x, y_abs, width, height,
                textColour=self.widget_text_color,
                font=self.font,
                colour=(64, 64, 64),
                borderColour=(0, 0, 0),
                borderThickness=border_thickness,
                placeholderText="Enter your name",
                onSubmit=self.ok_clicked
            )
            self.active_widgets[textbox_name] = textbox
        self.active_widgets[textbox_name].draw()

        y += (self.char_height + self.char_sep_height) * 4

        texts = ("OK",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_highscores(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        hsss = f"{self.high_scores_state}x{self.high_scores_state}"

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 15) / 2
        for text in ("HIGH SCORES", hsss, f"Rank Name{' '*(self.high_score_name_max_len-4)} Score"):
            width = len(text) * self.char_width
            x = (self.game_surf.get_width() - width) / 2
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height) * 2

        for i in range(5):
            if hsss in self.high_scores and i < len(self.high_scores[hsss]):
                cols = (
                    f"{i+1:>4}",
                    f"{self.high_scores[hsss][i][0]}{' '*(self.high_score_name_max_len-len(self.high_scores[hsss][i][0]))}",
                    f"{self.high_scores[hsss][i][1]:>5}"
                )
                text = f"{cols[0]} {cols[1]} {cols[2]}"
                width = len(text) * self.char_width
                x = (self.game_surf.get_width() - width) / 2
                label = self.font.render(text, True, self.widget_text_color)
                self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height)

        y += (self.char_height + self.char_sep_height) * 2

        texts = ("BACK",)
        self.draw_buttons(texts, y, 0, "game")

        for i, text in enumerate(("<", ">")):
            width = (len(text) + 2) * self.char_width
            height = (self.char_height + self.char_sep_height) * 5
            x = {0: self.char_width, 1: self.game_surf.get_width() - width - self.char_width}.get(i) + self.game_surf.get_abs_offset()[0]
            y = (self.game_surf.get_height() - height) / 2
            y_abs = y + self.game_surf.get_abs_offset()[1]
            border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
            if border_thickness < 1:
                border_thickness = 1
            button_name = {0: "left", 1: "right"}.get(i)
            if button_name not in self.active_widgets:
                button = pygamew.Button(
                    self.screen_surf, x, y_abs, width, height,
                    text=text,
                    textColour=self.widget_text_color,
                    font=self.font,
                    colour=(64, 64, 64),
                    hoverColour=(96, 96, 96),
                    pressedColour=(128, 128, 128),
                    borderColour=(0, 0, 0),
                    hoverBorderColour=(32, 32, 32),
                    pressedBorderColour=(64, 64, 64),
                    shadowColour=[val * 2 / 3 for val in self.background_color["game"]],
                    shadowDistance=self.char_sep_height // 2,
                    borderThickness=border_thickness,
                    onRelease=getattr(self, f"{button_name}_clicked")
                )
                self.active_widgets[button_name] = button
            self.active_widgets[button_name].draw()

    def draw_preferences(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 12) / 2
        height = self.char_height + self.char_sep_height
        texts = ("Background music", "Sound effects")
        text_width = max([len(text) for text in texts]) * self.char_width
        spacing_width = 3 * self.char_width
        toggle_width = 3 * self.char_width
        width = text_width + spacing_width + toggle_width
        x_text = (self.game_surf.get_width() - width) / 2
        x_toggle = x_text + text_width + spacing_width
        x_toggle_abs = x_toggle + self.game_surf.get_abs_offset()[0]
        for text in texts:
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x_text, y))
            y_abs = y + self.game_surf.get_abs_offset()[1]
            toggle_name = text.lower()
            toggle_name = toggle_name.replace(' ', '_')
            if toggle_name not in self.active_widgets:
                toggle = pygamew.Toggle(
                    self.screen_surf, int(x_toggle_abs), int(y_abs), int(toggle_width), int(height),
                    startOn = self.preferences.get(toggle_name, True),
                    onColour = (0, 255, 0),
                    offColour = (128, 128, 128),
                    handleOnColour = (0, 128, 0),
                    handleOffColour = (64, 64, 64)
                )
                self.active_widgets[toggle_name] = toggle
            self.active_widgets[toggle_name].draw()
            y += (self.char_height + self.char_sep_height) * 3

        y += (self.char_height + self.char_sep_height) * 4

        texts = ("SAVE",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_about(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 10) / 2
        for text in ("MATCH3PY", "AUTHOR: TOMAS GONZALEZ ARAGON"):
            width = len(text) * self.char_width
            x = (self.game_surf.get_width() - width) / 2
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height) * 4

        texts = ("BACK",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_screen(self) -> None:
        self.screen_surf.fill(self.background_color["screen"])

        if self.game_state == GameState.RUNNING:
            self.game_surf.fill(self.background_color["game"])
            self.draw_board()
            self.draw_sidebar()
        elif self.game_state == GameState.MAINMENU or self.game_state == GameState.PAUSED:
            self.draw_main_menu()
        elif self.game_state == GameState.CHOOSESIZE:
            self.draw_choosesize()
        elif self.game_state == GameState.ENDED:
            self.draw_ended()
        elif self.game_state == GameState.ENTERHIGHSCORE:
            self.draw_enterhighscore()
        elif self.game_state == GameState.HIGHSCORES:
            self.draw_highscores()
        elif self.game_state == GameState.PREFERENCES:
            self.draw_preferences()
        elif self.game_state == GameState.ABOUT:
            self.draw_about()

    ##################################################
    # Update functions
    ##################################################

    def update_board(self) -> None:
        self.draw_board()
        pygame.display.flip()

    def update_sidebar(self) -> None:
        self.draw_sidebar()
        pygame.display.flip()

    def update_screen(self) -> None:
        self.active_widgets = {}
        self.draw_screen()
        pygame.display.flip()

    ##################################################
    # On click functions
    ##################################################

    def new_game_clicked(self) -> None:
        self.game_state = GameState.CHOOSESIZE
        self.update_screen()

    def start_clicked(self) -> None:
        size = self.active_widgets["choose_board_size"].getSelected()
        if size is None:
            return
        num_values = size - 1
        if size > 7:
            num_values -= 1
        if size > 10:
            num_values -= 1
        self.board = Match3Board(size, size, num_values)
        self.score = 0
        self.time_left = self.time_init
        self.time_score = 0
        self.time_left_sec = int(self.time_left / 1000)
        self.hint = False
        self.hint_cut_score = False
        self.plus_score_ani_time_start = 0
        self.curr_plus_score_ani_time = self.plus_score_ani_time + 1
        self.curr_score = 0
        self.curr_time_score = 0
        self.time_paused = 0
        self.pause = False
        self.game_state = GameState.RUNNING
        self.start_music()
        self.resize_surfaces()
        self.update_screen()
        self.time_start = pygame.time.get_ticks()

    def hint_clicked(self) -> None:
        self.hint = True

    def pause_clicked(self) -> None:
        self.pause = True

    def resume_game_clicked(self) -> None:
        self.game_state = GameState.RUNNING
        self.start_music()
        self.update_screen()
        self.time_paused += pygame.time.get_ticks() - self.pause_time

    def continue_clicked(self) -> None:
        min_hs = 0
        hs = self.high_scores.get(f"{self.board.cols}x{self.board.rows}", list())
        if len(hs) > 0:
            min_hs = min([ns[1] for ns in hs])
        if self.score > 0 and (self.score > min_hs or len(hs) < 5):
            self.game_state = GameState.ENTERHIGHSCORE
            self.play_sound("yay")
        else:
            self.game_state = GameState.MAINMENU
        self.update_screen()

    def ok_clicked(self) -> None:
        name = self.active_widgets["high_score_name"].getText()
        # TODO: Sanitize name.
        if len(name) == 0:
            return
        hs = self.high_scores.get(f"{self.board.cols}x{self.board.rows}", list())
        hs.append([name, self.score])
        hs.sort(key=lambda d: d[1], reverse=True)
        if len(hs) > 5:
            del hs[-1]
        self.high_scores[f"{self.board.cols}x{self.board.rows}"] = hs
        with open(self.high_scores_filename, 'w') as f:
            json.dump(self.high_scores, f)
        self.game_state = GameState.MAINMENU
        self.update_screen()

    def high_scores_clicked(self) -> None:
        self.prev_state = self.game_state
        self.game_state = GameState.HIGHSCORES
        self.update_screen()

    def left_clicked(self) -> None:
        self.high_scores_state -= 1
        if self.high_scores_state < self.board_sizes[0]:
            self.high_scores_state = self.board_sizes[0]
        self.update_screen()

    def right_clicked(self) -> None:
        self.high_scores_state += 1
        if self.high_scores_state > self.board_sizes[-1]:
            self.high_scores_state = self.board_sizes[-1]
        self.update_screen()

    def preferences_clicked(self) -> None:
        self.prev_state = self.game_state
        self.game_state = GameState.PREFERENCES
        self.update_screen()

    def save_clicked(self) -> None:
        for s in ("background_music", "sound_effects"):
            self.preferences[s] = self.active_widgets[s].value
        with open(self.preferences_filename, 'w') as f:
            json.dump(self.preferences, f)
        self.game_state = self.prev_state
        self.update_screen()

    def about_clicked(self) -> None:
        self.prev_state = self.game_state
        self.game_state = GameState.ABOUT
        self.update_screen()

    def back_clicked(self) -> None:
        self.game_state = self.prev_state
        self.update_screen()

    def exit_clicked(self) -> None:
        pygame.quit()
        exit()

    ##################################################
    # Helper functions
    ##################################################

    def win_pos_to_board_pos(self, win_pos_x: int, win_pos_y: int, relative_to_window: bool = False) -> tuple[int, int]:
        if relative_to_window:
            win_pos_x -= self.board_surf.get_abs_offset()[0]
            win_pos_y -= self.board_surf.get_abs_offset()[1]
        col_w = self.board_surf.get_width() / self.board.cols
        row_h = self.board_surf.get_height() / self.board.rows
        board_pos_x = (win_pos_x - col_w / 2) / col_w
        board_pos_y = (win_pos_y - row_h / 2) / row_h
        return (int(round(board_pos_x)), int(round(board_pos_y)))

    def board_pos_to_win_pos(self, board_pos_x: int, board_pos_y: int, relative_to_window: bool = False) -> tuple[int, int]:
        col_w = self.board_surf.get_width() / self.board.cols
        row_h = self.board_surf.get_height() / self.board.rows
        win_pos_x = board_pos_x * col_w + col_w / 2
        win_pos_y = board_pos_y * row_h + row_h / 2
        if relative_to_window:
            win_pos_x += self.board_surf.get_abs_offset()[0]
            win_pos_y += self.board_surf.get_abs_offset()[1]
        return (int(win_pos_x), int(win_pos_y))

    def point_inside_circle(self, point: tuple[int, int], circle_center: tuple[int, int], r: float) -> bool:
        x, y = point
        c_x, c_y = circle_center
        return (x - c_x)**2 + (y - c_y)**2 < r**2

    def get_num_vertical_points(self, points: list[tuple[int, int]]) -> int:
        points_in_line = dict()
        for (col, _) in points:
            points_in_line[col] = points_in_line.get(col, 0) + 1
        return max(points_in_line.values())

    def play_sound(self, sound: str) -> None:
        if self.preferences.get("sound_effects", True) and sound in self.sounds:
            pygame.mixer.Sound.play(self.sounds[sound])

    def start_music(self) -> None:
        if self.preferences.get("background_music", True):
            try:
                pygame.mixer.music.play(-1, 0, 1000)
            except:
                pass

    ##################################################
    # Other functions
    ##################################################

    def resize_surfaces(self) -> None:
        # Calculate new screen size
        sw, sh = self.screen_surf.get_size()
        gw, gh = sw, sh
        gx, gy = 0, 0
        if sw / sh > self.game_ratio:
            gw = sh * self.game_ratio
            gx = (sw - gw) / 2
        else:
            gh = sw / self.game_ratio
            gy = (sh - gh) / 2
        self.game_surf = self.screen_surf.subsurface((gx, gy, gw, gh))
        # Calculate and update new board size and new circle radius
        pos = gh * (1 - self.board_scale) / 2
        side = gh * self.board_scale
        self.board_surf = self.game_surf.subsurface((pos, pos, side, side))
        if self.board is not None:
            self.circle_radius = self.board_surf.get_height() / self.board.cols / 2
        # Calculate and update new sidebar size
        self.sidebar_surf = self.game_surf.subsurface((gh, 0, gw - gh, gh))
        # Calculate and update new font size
        self.font_size = self.min_font_size * self.game_surf.get_width() / self.starting_width
        self.char_width = self.min_char_width * self.game_surf.get_width() / self.starting_width
        self.char_height = self.min_char_height * self.game_surf.get_height() / self.starting_height
        self.char_sep_height = self.min_char_sep_height * self.game_surf.get_height() / self.starting_height
        self.font = pygame.font.SysFont("monospace", int(self.font_size))
        self.font.set_bold(True)
        # Clear active widgets to force a re-draw
        self.active_widgets = {}

    ##################################################
    # Process events functions
    ##################################################

    def choosesize_process_events(self, events, **kwargs) -> bool:
        self.active_widgets["choose_board_size"].listen(events)
        self.draw_choosesize()
        if self.active_widgets["choose_board_size"].dropped:
            self.active_widgets["start"].hide()
        else:
            self.active_widgets["start"].show()
        return True

    def running_process_events(self, events, **kwargs) -> bool:
        # End the game if the time has run out
        if self.time_left <= 0:
            self.game_ended = True

        update_display = False

        # Update the time left
        self.time_left = self.time_paused + self.time_init + self.time_score - (pygame.time.get_ticks() - self.time_start)
        if self.time_left_sec != int(round(self.time_left / 1000)):
            self.time_left_sec = int(round(self.time_left / 1000))
            if self.time_left_sec < 0:
                self.time_left_sec = 0
            self.draw_sidebar()
            update_display = True

        # Play beep sound
        if self.time_left_sec <= 5:
            if pygame.time.get_ticks() - self.last_beep_sound_time >= 1000:
                self.last_beep_sound_time = pygame.time.get_ticks()
                self.play_sound("beep")

        # Remove plus score from sidebar if the ani time is up
        if self.curr_plus_score_ani_time <= self.plus_score_ani_time:
            self.curr_plus_score_ani_time = pygame.time.get_ticks() - self.plus_score_ani_time_start
            if self.curr_plus_score_ani_time > self.plus_score_ani_time:
                self.draw_sidebar()
                update_display = True

        # Process events
        if not kwargs.get('mouse', False):
            return
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.WAITING:
                    self.board_pos_src = self.win_pos_to_board_pos(*event.pos, True)
                    if self.board.out_of_bounds(*self.board_pos_src):
                        continue
                    # Check that the mouse is inside a circle
                    circle_center = self.board_pos_to_win_pos(*self.board_pos_src, True)
                    pic = self.point_inside_circle(event.pos, circle_center, self.circle_radius * self.circle_scale)
                    if pic:
                        self.mouse_state = MouseState.PRESSED
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_state == MouseState.PRESSED:
                    self.mouse_state = MouseState.MOVING
                if self.mouse_state == MouseState.MOVING:
                    board_pos_dst = list(self.win_pos_to_board_pos(*event.pos, True))
                    # Check that the mouse was dragged to a different position in the board
                    if list(self.board_pos_src) == board_pos_dst:
                        continue
                    # If the mouse went to far, move the dst pos back to a neighbor
                    for i in range(2):
                        if self.board_pos_src[i] - board_pos_dst[i] > 1:
                            board_pos_dst[i] = self.board_pos_src[i] - 1
                        elif self.board_pos_src[i] - board_pos_dst[i] < -1:
                            board_pos_dst[i] = self.board_pos_src[i] + 1
                    if self.board.out_of_bounds(*board_pos_dst):
                        continue
                    # Check that the new position is a neighbor
                    swap_valid = False
                    for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        neigh_x = self.board_pos_src[0] + x
                        neigh_y = self.board_pos_src[1] + y
                        if [neigh_x, neigh_y] == board_pos_dst:
                            swap_valid = True
                            break
                    if not swap_valid:
                        self.mouse_state = MouseState.WAITING
                        continue
                    # Do the swap, if it was not a valid play, revert it
                    swap_valid = self.board.is_swap_valid(self.board_pos_src, board_pos_dst)
                    self.animate_swap(self.board_pos_src, tuple(board_pos_dst))
                    self.board.swap(self.board_pos_src, board_pos_dst)
                    if not swap_valid:
                        self.animate_swap(tuple(board_pos_dst), self.board_pos_src)
                        self.board.swap(board_pos_dst, self.board_pos_src)
                    self.mouse_state = MouseState.WAITING
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.PRESSED:
                    self.mouse_state = MouseState.WAITING
                elif self.mouse_state == MouseState.MOVING:
                    self.mouse_state = MouseState.WAITING

        return update_display

    def enterhighscore_process_events(self, events, **kwargs) -> bool:
        self.active_widgets["high_score_name"].listen(events)
        self.draw_screen()
        return True

    def preferences_process_events(self, events, **kwargs) -> bool:
        self.active_widgets["background_music"].listen(events)
        self.active_widgets["sound_effects"].listen(events)
        self.draw_screen()
        return True

    def process_events(self, fps: int = -1, **kwargs) -> bool:
        # Wait until frame time
        if fps < 0:
            fps = self.ani_fps
        self.clock.tick(fps)

        # Process generic events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.resize_surfaces()
                return True
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()

        # Process specific events related to the current game state
        gs = self.game_state.name
        gs = gs.lower()
        try:
            func = getattr(self, f"{gs}_process_events")
        except AttributeError:
            func = None
        update_display = False
        if func is not None:
            update_display = func(events, **kwargs)

        # Listen to button events
        for button in self.active_widgets.values():
            if type(button) == pygamew.Button:
                color = button.colour
                button.listen(events)
                if color != button.colour:
                    button.draw()
                    update_display = True

        if update_display:
            pygame.display.flip()

        return False

    ##################################################
    # Main game loop functions
    ##################################################

    def running(self) -> None:
        # Let the computer play (for debug)
        # play = self.board.find_better_play()
        # if len(play) > 0:
        #     (swap_points, groups) = play
        #     self.animate_swap(swap_points[0], swap_points[1])
        #     self.board.swap(swap_points[0], swap_points[1])

        # Find all the match3 groups and update the board state by
        # clearing them and then filling the board with new tiles from the top
        # while shifting down the ones floating
        # Do this until the board state is stabilized
        groups = self.board.get_valid_groups()
        bonus_score = 0
        bonus = 0
        while len(groups) > 0:
            # Clear any old plus score in the sidbar
            self.animate_plus_score_prev()
            # Calculate the score from the match3 groups, add extra time poportional to the score
            self.curr_score = self.board.calc_score(groups) + bonus_score
            group_bonus_score = 0
            group_bonus = 0
            for _ in range(len(groups) - 1):
                group_bonus += 1
                group_bonus_score += group_bonus
            self.curr_time_score = ((self.curr_score + bonus_score + group_bonus_score) * 100)
            if self.hint_cut_score:
                self.curr_score //= 2
                self.curr_time_score = self.curr_score * 100
                self.hint_cut_score = False
            self.score += self.curr_score
            self.time_score += self.curr_time_score
            # Show plus score in the sidebar
            self.animate_plus_score_post()
            # Clear the tiles that create a match3 group
            points = [point for group in groups for point in group]
            self.animate_clear(points)
            self.board.clear(points)
            # Shift down the tiles that are floating and create new tiles in the top row
            # Do this until the board is filled
            while not self.board.is_full():
                shifted = self.board.shift_down()
                shifted += self.board.populate(rows=[0, 1], no_valid_play_check=False, no_match3_group_check=False)
                self.animate_shift_down(shifted, self.get_num_vertical_points(points))
            self.play_sound("drop")
            groups = self.board.get_valid_groups()
            bonus += 1
            bonus_score += bonus

        # Check if there is a valid play, if not, regenerate the board
        play = self.board.find_a_play()
        if len(play) == 0:
            self.animate_clear([(x, y) for y in range(self.board.rows) for x in range(self.board.cols)], True)
            self.board.clear()
            try:
                self.board.populate()
            except RecursionError:
                print(f"FATAL: Couldn't regenerate the the board.")
                pygame.quit()
                exit(1)
            self.update_board()

        if self.hint:
            self.hint = False
            play = self.board.find_a_play()
            if len(play) > 0:
                (swap_points, groups) = play
                self.animate_hint(*swap_points)
            self.hint_cut_score = True
        if self.game_ended:
            self.game_ended = False
            self.game_state = GameState.ENDED
            self.play_sound("end")
            pygame.mixer.music.fadeout(1000)
            self.update_screen()
        elif self.pause:
            self.pause = False
            self.game_state = GameState.PAUSED
            self.music_pos = pygame.mixer.music.get_pos()
            pygame.mixer.music.fadeout(1000)
            self.update_screen()
            self.pause_time = pygame.time.get_ticks()

    def run(self) -> None:
        # Load high scores and preferences
        for name in ("high_scores", "preferences"):
            filename = getattr(self, f"{name}_filename")
            schema = getattr(self, f"{name}_schema")
            data = dict()
            try:
                with open(filename, 'r') as file:
                    try:
                        data = json.load(file)
                        try:
                            jsonschema.validate(data, schema)
                        except jsonschema.ValidationError:
                            print(f"ERROR: In file {filename}: json doesn't conform to schema.")
                    except json.JSONDecodeError:
                        print(f"ERROR: In file {filename}: json not valid.")
            except FileNotFoundError:
                pass
            setattr(self, name, data)

        pygame.init()
        pygame.mixer.init()
        self.font = pygame.font.SysFont("monospace", int(self.font_size))
        self.font.set_bold(True)
        self.clock = pygame.time.Clock()
        icon = pygame.image.load("icon32x32.png")
        pygame.display.set_icon(icon)
        pygame.display.set_caption("MATCH3PY")
        self.screen_surf = pygame.display.set_mode((self.starting_width, self.starting_height), self.flags, vsync=1)
        self.resize_surfaces()
        self.update_screen()

        # Load audio
        if os.path.isfile(self.background_music_filename):
            pygame.mixer.music.load(self.background_music_filename)
        if os.path.isdir(self.sounds_dir):
            for filename in os.listdir(self.sounds_dir):
                sound_name = os.path.splitext(filename)[0]
                self.sounds[sound_name] = pygame.mixer.Sound(f"{self.sounds_dir}/{filename}")

        while True:
            if self.process_events(fps=self.main_loop_refresh_rate, mouse=True):
                self.update_screen()

            if self.game_state == GameState.RUNNING:
                self.running()
