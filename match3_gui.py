import pygame
from pygame import gfxdraw
from enum import Enum, auto
from match3_board import Match3Board

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
    border_color = (32, 32, 32)
    background_color = {
        "screen": (0, 0, 0),
        "game": (16, 16, 16),
        "board": (0, 0, 0),
        "sidebar": (32, 32, 32),
    }
    min_width = 640
    min_height = 480
    game_ratio = 4 / 3
    board_scale = 0.9
    swap_ani_time = 200
    shift_down_ani_time = 200
    clear_ani_time = 200
    ani_fps = 360
    main_loop_refresh_rate = 30
    circle_line_thickness = 19 / 20
    flags = pygame.RESIZABLE | pygame.HWSURFACE

    def __init__(self, side_len: int = 7) -> None:
        if side_len < 5:
            raise ValueError("Minimum size is 5.")
        if side_len > 13:
            raise ValueError("Maximum size is 13.")
        self.board = Match3Board(side_len, side_len, side_len-1)
        self.circle_radius = 0
        self.screen_surf = None
        self.game_surf = None
        self.board_surf = None
        self.sidebar_surf = None
        self.clock = None
        self.mouse_state = MouseState.WAITING
        self.board_pos_src = None
        self.score = 0
        self.curr_score = 0
        self.time_init = 60000
        self.time_left = self.time_init
        self.time_start = 0
        self.time_score = 0
        self.curr_time_score = 0
        self.prev_time_left_sec = self.time_left // 1000

    def win_pos_to_board_pos(self, win_pos_x: int, win_pos_y: int) -> tuple[int, int]:
        shift = self.board_surf.get_width() * (1 - self.board_scale) / 2
        win_pos_x -= shift
        win_pos_y -= shift
        col_w = self.board_surf.get_width() / self.board.cols
        row_h = self.board_surf.get_height() / self.board.rows
        board_pos_x = (win_pos_x - col_w / 2) / col_w
        board_pos_y = (win_pos_y - row_h / 2) / row_h
        return (int(round(board_pos_x)), int(round(board_pos_y)))

    def board_pos_to_win_pos(self, board_pos_x: int, board_pos_y: int, shift: bool = False) -> tuple[int, int]:
        col_w = self.board_surf.get_width() / self.board.cols
        row_h = self.board_surf.get_height() / self.board.rows
        win_pos_x = board_pos_x * col_w + col_w / 2
        win_pos_y = board_pos_y * row_h + row_h / 2
        if shift:
            shift = self.board_surf.get_width() * (1 - self.board_scale) / 2
        else:
            shift = 0
        return (int(win_pos_x + shift), int(win_pos_y + shift))

    def point_inside_circle(self, point: tuple[int, int], circle_center: tuple[int, int], r) -> bool:
        x, y = point
        c_x, c_y = circle_center
        return (x - c_x)**2 + (y - c_y)**2 < r**2

    def draw_circle(self, x, y, color, radius = None) -> None:
        if radius is None:
            radius = self.circle_radius
        if color != (0, 0, 0):
            gfxdraw.aacircle(self.board_surf, x, y, int(radius * self.circle_line_thickness), color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius * self.circle_line_thickness), color)
        else:
            gfxdraw.aacircle(self.board_surf, x, y, int(radius * self.circle_line_thickness), self.border_color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius * self.circle_line_thickness), self.border_color)
            gfxdraw.aacircle(self.board_surf, x, y, int(radius * (1 - (1 - self.circle_line_thickness) * 2)), color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius * (1 - (1 - self.circle_line_thickness) * 2)), color)

    def animate_swap(self, board_point1: tuple[int, int], board_point2: tuple[int, int]) -> None:
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

            self.game_surf.blit(self.board_surf, (self.board_surf.get_width() * (1 - self.board_scale) / 2, self.board_surf.get_height() * (1 - self.board_scale) / 2))
            self.screen_surf.blit(self.game_surf, (0, 0))
            pygame.display.flip()

    def animate_clear(self, board_points: list[tuple[int, int]]) -> None:
        win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

        target_transparency = 0
        target_size = 0
        curr_transparency = 255
        curr_size = self.circle_radius

        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while curr_transparency != target_transparency or curr_size != target_size:
            if self.process_events():
                win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

            self.draw_board(no_draw_pts=board_points)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            # Calculate the new size and the new transparency
            curr_transparency = int(target_transparency * (1 - curr_ani_time / self.clear_ani_time))
            if curr_transparency > target_transparency:
                curr_transparency = target_transparency
            curr_size = int(self.circle_radius * (1 - curr_ani_time / self.clear_ani_time))
            if curr_size < target_size:
                curr_size = target_size

            # Draw the moving circles
            for i, p in enumerate(board_points):
                color_index = self.board.board[p[1]][p[0]]
                if color_index < 0:
                    continue
                self.draw_circle(win_points[i][0], win_points[i][1], self.colors[color_index], curr_size)

            self.game_surf.blit(self.board_surf, (self.board_surf.get_width() * (1 - self.board_scale) / 2, self.board_surf.get_height() * (1 - self.board_scale) / 2))
            self.screen_surf.blit(self.game_surf, (0, 0))
            pygame.display.flip()

    def animate_shift_down(self, shifted_bp: list[tuple[int, int]], num_vertical_points: int) -> None:
        board_points_dst = shifted_bp
        board_points_src = [(x, y - 1) for (x, y) in board_points_dst]
        win_points_dst = [list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
        win_points_src = [list(self.board_pos_to_win_pos(*p)) for p in board_points_src]
        color_indices = [self.board.board[y][x] for (x, y) in board_points_dst]

        curr_pos = [[x, y] for (x, y) in win_points_src]

        ani_time = self.shift_down_ani_time / num_vertical_points
        if ani_time < 100:
            ani_time = 100
        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while any([curr_pos[i] != win_points_dst[i] for i in range(len(curr_pos))]):
            if self.process_events():
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

            self.game_surf.blit(self.board_surf, (self.board_surf.get_width() * (1 - self.board_scale) / 2, self.board_surf.get_height() * (1 - self.board_scale) / 2))
            self.screen_surf.blit(self.game_surf, (0, 0))
            pygame.display.flip()

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

    def draw_sidebar(self) -> None:
        min_font_size = 20
        min_char_width = 13.8
        min_char_sep_width = 0
        min_char_height = 13.8
        min_char_sep_height = min_char_height / 2

        font_size = min_font_size * self.game_surf.get_width() / self.min_width
        char_width = min_char_width * self.game_surf.get_width() / self.min_width
        char_sep_width = min_char_sep_width * self.game_surf.get_width() / self.min_width
        char_height = min_char_height * self.game_surf.get_height() / self.min_height
        char_sep_height = min_char_sep_height * self.game_surf.get_height() / self.min_height

        self.sidebar_surf.fill(self.background_color["sidebar"])
        font = pygame.font.SysFont("monospace", int(font_size))
        font.set_bold(True)

        y = self.sidebar_surf.get_height() * 0.2
        for text in ("SCORE", str(self.score), "TIME LEFT", str(self.prev_time_left_sec)):
            if text == "TIME LEFT":
                y += char_height + char_sep_height
            label = font.render(text, True, (224,224,224))
            width = len(text) * char_width + (len(text) - 1) * char_sep_width
            x = (self.sidebar_surf.get_width() - width) / 2
            self.sidebar_surf.blit(label, (x, y))
            y += char_height + char_sep_height

    def update_sidebar(self) -> None:
        self.draw_sidebar()
        self.game_surf.blit(self.sidebar_surf, (self.game_surf.get_height(), 0))
        self.screen_surf.blit(self.game_surf, (0, 0))
        pygame.display.flip()

    def update_screen(self) -> None:
        self.screen_surf.fill(self.background_color["screen"])
        self.game_surf.fill(self.background_color["game"])
        self.draw_board()
        self.draw_sidebar()
        self.game_surf.blit(self.board_surf, (self.board_surf.get_width() * (1 - self.board_scale) / 2, self.board_surf.get_height() * (1 - self.board_scale) / 2))
        self.game_surf.blit(self.sidebar_surf, (self.game_surf.get_height(), 0))
        self.screen_surf.blit(self.game_surf, (0, 0))
        pygame.display.flip()

    def process_events(self, fps: int = -1, mouse: bool = False) -> bool:
        # Wait until frame time
        if fps < 0:
            fps = self.ani_fps
        self.clock.tick(fps)

        # Update the time left
        self.time_left = self.time_init + self.time_score - (pygame.time.get_ticks() - self.time_start)

        if self.prev_time_left_sec != int(round(self.time_left / 1000)):
            self.prev_time_left_sec = int(round(self.time_left / 1000))
            if self.prev_time_left_sec < 0:
                self.prev_time_left_sec = 0
            self.update_sidebar()

        if self.time_left <= 0:
            print(f"Time's up. Final score: {self.score}")
            pygame.quit()
            exit()

        # Process events
        ret = False
        for event in pygame.event.get():
            if mouse and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.WAITING:
                    self.board_pos_src = self.win_pos_to_board_pos(*event.pos)
                    # Check that the mouse is inside a circle
                    circle_center = self.board_pos_to_win_pos(*self.board_pos_src, shift=True)
                    pic = self.point_inside_circle(event.pos, circle_center, int(self.circle_radius * self.circle_line_thickness))
                    if pic:
                        self.mouse_state = MouseState.PRESSED
            elif mouse and event.type == pygame.MOUSEMOTION:
                if self.mouse_state == MouseState.PRESSED:
                    self.mouse_state = MouseState.MOVING
                if self.mouse_state == MouseState.MOVING:
                    board_pos_dst = self.win_pos_to_board_pos(*event.pos)
                    # Check that the mouse was dragged to a different position in the board
                    if self.board_pos_src == board_pos_dst:
                        continue
                    # Check that the new position is a neighbor
                    swap_valid = False
                    for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        neigh_x = self.board_pos_src[0] + x
                        neigh_y = self.board_pos_src[1] + y
                        if (neigh_x, neigh_y) == board_pos_dst:
                            swap_valid = True
                            break
                    if not swap_valid:
                        print(f"Swap not valid: destination is not a neighbor.")
                        self.mouse_state = MouseState.WAITING
                        continue
                    circle_center = self.board_pos_to_win_pos(*board_pos_dst, shift=True)
                    pic = self.point_inside_circle(event.pos, circle_center, int(self.circle_radius * self.circle_line_thickness))
                    # Check that the mouse is inside the neighbor's circle
                    if pic:
                        # Do the swap, if it was not a valid play, revert it
                        swap_valid = self.board.is_swap_valid(self.board_pos_src, board_pos_dst)
                        self.animate_swap(self.board_pos_src, board_pos_dst)
                        self.board.swap(self.board_pos_src, board_pos_dst)
                        if not swap_valid:
                            print(f"Swap not valid: No match3 groups found.")
                            self.animate_swap(board_pos_dst, self.board_pos_src)
                            self.board.swap(board_pos_dst, self.board_pos_src)
                        self.mouse_state = MouseState.WAITING
            elif mouse and event.type == pygame.MOUSEBUTTONUP:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.PRESSED:
                    self.mouse_state = MouseState.WAITING
                elif self.mouse_state == MouseState.MOVING:
                    self.mouse_state = MouseState.WAITING
            elif event.type == pygame.VIDEORESIZE:
                # Calculate new screen size
                sw, sh = event.size
                if event.w < self.min_width:
                    sw = self.min_width
                if event.h < self.min_height:
                    sh = self.min_height
                # Calculate and update new game size
                gw, gh = sw, sh
                if sw / sh > self.game_ratio:
                    gw = int(sh * self.game_ratio)
                else:
                    gh = int(sw / self.game_ratio)
                self.game_surf = pygame.Surface((gw, gh), pygame.HWSURFACE)  # Update game surface
                # Calculate and update new board size and new circle radius
                bw, bh = gh, gh
                bw, bh = int(bw * self.board_scale), int(bh * self.board_scale)
                self.board_surf = pygame.Surface((bw, bh), pygame.HWSURFACE)  # Update board surface
                self.circle_radius = self.board_surf.get_width() / self.board.cols / 2
                # Calculate and update new sidebar size
                sbw, sbh = gw - gh, gh
                self.sidebar_surf = pygame.Surface((sbw, sbh), pygame.HWSURFACE)  # Update sidebar surface
                # Update screen surface
                self.screen_surf = pygame.display.set_mode((sw, sh), self.flags, vsync=1)
                # Fill surfaces with background color
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.board_surf.fill(self.background_color["board"])
                self.sidebar_surf.fill(self.background_color["sidebar"])
                ret = True
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()
        return ret

    def get_num_vertical_points(self, points: list[tuple[int, int]]) -> int:
        points_in_line = dict()
        for (col, _) in points:
            points_in_line[col] = points_in_line.get(col, 0) + 1
        return max(points_in_line.values())

    def run(self) -> None:
        pygame.init()
        self.clock = pygame.time.Clock()

        self.screen_surf = pygame.display.set_mode((self.min_width, self.min_height), self.flags, vsync=1)
        self.game_surf = pygame.Surface((self.min_width, self.min_height), pygame.HWSURFACE)
        bw, bh = int(self.min_height * self.board_scale), int(self.min_height * self.board_scale)
        self.board_surf = pygame.Surface((bw, bh), pygame.HWSURFACE)
        self.sidebar_surf = pygame.Surface((self.min_width - self.min_height, self.min_height), pygame.HWSURFACE)
        self.circle_radius = self.board_surf.get_width() / self.board.cols / 2

        self.update_screen()
        self.time_start = pygame.time.get_ticks()

        while True:
            if self.process_events(fps=self.main_loop_refresh_rate, mouse=True):
                self.update_screen()

            # Find all the match3 groups and update the board state by
            # clearing them and then filling the board with new tiles from the top
            # while shifting down the ones floating
            # Do this until the board state is stabilized
            groups = self.board.get_valid_groups()
            while len(groups) > 0:
                # Calculate the score from the match3 groups, add extra time poportional to the score
                self.curr_score = self.board.calc_score(groups)
                self.score += self.curr_score
                self.curr_time_score = self.curr_score * 100
                self.time_score += self.curr_time_score
                self.update_sidebar()
                # Clear the tiles that create a match3 group
                points = [point for group in groups for point in group]
                self.animate_clear(points)
                self.board.clear(points)
                # Shift down the tiles that are floating and create new tiles in the top row
                # Do this until the board is filled
                num_vertical_points = self.get_num_vertical_points(points)
                while not self.board.is_full():
                    shifted = self.board.shift_down()
                    shifted += self.board.populate(rows=[0, 1], no_valid_play_check=False, no_match3_group_check=False)
                    self.animate_shift_down(shifted, num_vertical_points)
                groups = self.board.get_valid_groups()

            # Check if there is a valid play, if not, regenerate the board
            play = self.board.find_a_play()
            if len(play) == 0:
                print(f"No more moves. Regenerating the board.")
                self.animate_clear([(x, y) for y in range(self.board.rows) for x in range(self.board.cols)])
                self.board.clear()
                try:
                    self.board.populate()
                except RecursionError:
                    print(f"FATAL: Couldn't regenerate the the board.")
                    pygame.quit()
                    exit(1)
                self.update_screen()

            # Let the computer play (for debug)
            # play = self.board.find_better_play()
            # if len(play) > 0:
            #     (swap_points, groups) = play
            #     print(f"Bot swapping {swap_points[0]} with {swap_points[1]}.")
            #     self.animate_swap(swap_points[0], swap_points[1])
            #     self.board.swap(swap_points[0], swap_points[1])
