import os
import pygame
from enum import Enum, auto
from match3_board import Match3Board

class MouseState(Enum):
    WAITING = auto()
    PRESSED = auto()
    MOVING = auto()


class Match3GUI:
    colors = [
        [128,  0,  0],  # 800000 Dark Red
        [  0,  0,128],  # 000080 Dark Blue
        [255,255,  0],  # FFFF00 Yellow
        [  0,128,  0],  # 008000 Green
        [ 84, 84, 84],  # 545454 Grey
        [192,  0,192],  # C000C0 Purple-Magenta
        [ 48,192,192],  # 30C0C0 Greyed Cyan
        [192,255,128],  # C0FF80 Pale Green-Yellow
        [255, 64, 64],  # FF4040 Light Red
        [172,172,255],  # ACACFF Light Blue
        [255,255,255],  # FFFFFF White
        [  0,  0,  0],  # 000000 Black
    ]
    border_color = (0, 0, 0)
    background_color = (255, 255, 255)
    min_width = 500
    min_height = 500
    ani_time = 150
    target_fps = 60
    flags = pygame.RESIZABLE

    def __init__(self, side_len: int = 13) -> None:
        if side_len < 5:
            raise ValueError("Minimum size is 5.")
        if side_len > 13:
            raise ValueError("Maximum size is 13.")
        self.board = Match3Board(side_len, side_len, side_len-1)
        self.size = self.width, self.height = self.min_width, self.min_height
        self.circle_radius = self.width / self.board.cols / 2
        self.screen = None
        self.clock = None
        self.mouse_state = MouseState.WAITING
        self.board_pos_src = None

    def win_pos_to_board_pos(self, win_pos_x: int, win_pos_y: int) -> tuple[int, int]:
        col_w = self.width / self.board.cols
        row_h = self.height / self.board.rows
        board_pos_x = (win_pos_x - col_w / 2) / col_w
        board_pos_y = (win_pos_y - row_h / 2) / row_h
        return (int(round(board_pos_x)), int(round(board_pos_y)))

    def board_pos_to_win_pos(self, board_pos_x: int, board_pos_y: int) -> tuple[int, int]:
        col_w = self.width / self.board.cols
        row_h = self.height / self.board.rows
        win_pos_x = board_pos_x * col_w + col_w / 2
        win_pos_y = board_pos_y * row_h + row_h / 2
        return (int(win_pos_x), int(win_pos_y))

    def point_inside_circle(self, point: tuple[int, int], circle_center: tuple[int, int], r) -> bool:
        x, y = point
        c_x, c_y = circle_center
        return (x - c_x)**2 + (y - c_y)**2 < r**2

    def animate_swap(self, board_point1: tuple[int, int], board_point2: tuple[int, int]) -> None:
        board_points = (board_point1, board_point2)
        win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))

        target_dist = (
            [win_points[1][0] - win_points[0][0], win_points[1][1] - win_points[0][1]],  # [dst_p1_x - src_p1_x, dst_p1_y - src_p1_y]
            [win_points[0][0] - win_points[1][0], win_points[0][1] - win_points[1][1]],  # [dst_p2_x - src_p2_x, dst_p2_y - src_p2_y]
        )
        curr_pos = [list(win_points[0]), list(win_points[1])]

        curr_ani_time = 0
        curr_time = pygame.time.get_ticks()
        ani_time_start = curr_time

        while curr_pos[0] != win_points[1] or curr_pos[1] != win_points[0]:  # curr_p1 != dst_p1 or curr_p2 != dst_p2
            if self.process_events():
                win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))
                target_dist = (
                    [win_points[1][0] - win_points[0][0], win_points[1][1] - win_points[0][1]],  # [dst_p1_x - src_p1_x, dst_p1_y - src_p1_y]
                    [win_points[0][0] - win_points[1][0], win_points[0][1] - win_points[1][1]],  # [dst_p2_x - src_p2_x, dst_p2_y - src_p2_y]
                )

            self.clock.tick(self.target_fps)
            self.screen.fill(self.background_color)
            self.draw_board(no_draw_pts=board_points)

            curr_time = pygame.time.get_ticks()
            curr_ani_time = curr_time - ani_time_start

            for p_i in reversed(range(2)):
                # Calculate the new position
                src_pos = win_points[p_i]
                dst_pos = win_points[int(not p_i)]
                curr_dist = (target_dist[p_i][0] * curr_ani_time / self.ani_time, target_dist[p_i][1] * curr_ani_time / self.ani_time)
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
                color = self.colors[color_index]
                pygame.draw.circle(self.screen, self.border_color, curr_pos[p_i], int(self.circle_radius))
                pygame.draw.circle(self.screen, color, curr_pos[p_i], int(self.circle_radius * 9 / 10))

            pygame.display.flip()

    def animate_clear(self, board_points: list[tuple[int, int]]) -> None:
        win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

        target_transparency = 0
        target_size = 0
        curr_transparency = 255
        curr_size = self.circle_radius

        curr_ani_time = 0
        curr_time = pygame.time.get_ticks()
        ani_time_start = curr_time

        while curr_transparency != target_transparency or curr_size != target_size:
            if self.process_events():
                win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

            self.clock.tick(self.target_fps)
            self.screen.fill(self.background_color)
            self.draw_board(no_draw_pts=board_points)

            curr_time = pygame.time.get_ticks()
            curr_ani_time = curr_time - ani_time_start

            # Calculate the new size and the new transparency
            curr_transparency = int(target_transparency * (1 - curr_ani_time / self.ani_time))
            if curr_transparency > target_transparency:
                curr_transparency = target_transparency
            curr_size = int(self.circle_radius * (1 - curr_ani_time / self.ani_time))
            if curr_size < target_size:
                curr_size = target_size

            for i, p in enumerate(board_points):
                # Draw the moving circles
                color_index = self.board.board[p[1]][p[0]]
                if color_index < 0:
                    continue
                color = self.colors[color_index]
                pygame.draw.circle(self.screen, list(self.border_color) + [curr_transparency], win_points[i], int(curr_size))
                pygame.draw.circle(self.screen, list(color) + [curr_transparency], win_points[i], int(curr_size * 9 / 10))

            pygame.display.flip()

    def animate_shift_down(self, shifted_bp: list[tuple[int, int]]) -> None:
        board_points_dst = shifted_bp
        board_points_src = [(x, y - 1) for (x, y) in board_points_dst]
        win_points_dst = [list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
        win_points_src = [list(self.board_pos_to_win_pos(*p)) for p in board_points_src]
        color_indices = [self.board.board[y][x] for (x, y) in board_points_dst]

        curr_pos = [[x, y] for (x, y) in win_points_src]

        curr_ani_time = 0
        curr_time = pygame.time.get_ticks()
        ani_time_start = curr_time

        while any([curr_pos[i] != win_points_dst[i] for i in range(len(curr_pos))]):
            if self.process_events():
                win_points_dst = [list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
                win_points_src = [list(self.board_pos_to_win_pos(*p)) for p in board_points_src]

            self.clock.tick(self.target_fps)
            self.screen.fill(self.background_color)
            self.draw_board(no_draw_pts=board_points_src + board_points_dst)

            curr_time = pygame.time.get_ticks()
            curr_ani_time = curr_time - ani_time_start

            for p_i in range(len(curr_pos)):
                # Calculate the new position
                src_pos = win_points_src[p_i]
                dst_pos = win_points_dst[p_i]
                target_dist = ((dst_pos[0] - src_pos[0]), (dst_pos[1] - src_pos[1]))
                curr_dist = (target_dist[0] * curr_ani_time / self.ani_time, target_dist[1] * curr_ani_time / self.ani_time)
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
                color = self.colors[color_index]
                pygame.draw.circle(self.screen, self.border_color, curr_pos[p_i], int(self.circle_radius))
                pygame.draw.circle(self.screen, color, curr_pos[p_i], int(self.circle_radius * 9 / 10))

            pygame.display.flip()

    def draw_board(self, no_draw_pts: list[tuple[int, int]] = None) -> None:
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                if no_draw_pts is not None and (col, row) in no_draw_pts:
                    continue
                color_index = self.board.board[row][col]
                if color_index < 0:
                    continue
                color = self.colors[color_index]
                pos = self.board_pos_to_win_pos(col, row)
                pygame.draw.circle(self.screen, self.border_color, pos, int(self.circle_radius))
                pygame.draw.circle(self.screen, color, pos, int(self.circle_radius * 9 / 10))

    def update_board(self) -> None:
        self.clock.tick(self.target_fps)
        self.screen.fill(self.background_color)
        self.draw_board()
        pygame.display.flip()

    def process_events(self, mouse: bool = False) -> bool:
        ret = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.VIDEORESIZE:
                self.width = min(event.size)
                if self.width < self.min_width:
                    self.width = self.min_width
                self.height = self.width
                scale = self.width / self.size[0]
                self.size = (self.width, self.height)
                self.circle_radius = self.circle_radius * scale
                self.screen = pygame.display.set_mode(self.size, self.flags, vsync=1)
                ret = True
            elif mouse and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.WAITING:
                    self.board_pos_src = self.win_pos_to_board_pos(*event.pos)
                    # Check that the mouse is inside a circle
                    circle_center = self.board_pos_to_win_pos(*self.board_pos_src)
                    pic = self.point_inside_circle(event.pos, circle_center, int(self.circle_radius * 9 / 10))
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
                    circle_center = self.board_pos_to_win_pos(*board_pos_dst)
                    pic = self.point_inside_circle(event.pos, circle_center, int(self.circle_radius * 9 / 10))
                    # Check that the mouse is inside the neighbor's circle
                    if pic:
                        # Check that the swap is valid and run the animation
                        swap_valid = self.board.is_swap_valid(self.board_pos_src, board_pos_dst)
                        self.animate_swap(self.board_pos_src, board_pos_dst)
                        self.board.swap(self.board_pos_src, board_pos_dst)
                        self.update_board()
                        if swap_valid:
                            # Swap is valid, do the swap in the board state
                            print(f"Swapping {self.board_pos_src} with {board_pos_dst}.")
                        else:
                            # Swap is not valid, revert the swap
                            print(f"Swap not valid: No match3 groups found.")
                            self.animate_swap(board_pos_dst, self.board_pos_src)
                            self.board.swap(board_pos_dst, self.board_pos_src)
                            #self.update_board()
                        self.mouse_state = MouseState.WAITING
            elif mouse and event.type == pygame.MOUSEBUTTONUP:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.PRESSED:
                    self.mouse_state = MouseState.WAITING
                elif self.mouse_state == MouseState.MOVING:
                    self.mouse_state = MouseState.WAITING
        return ret

    def run(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(self.size, self.flags, vsync=1)
        self.clock = pygame.time.Clock()

        self.update_board()

        while True:
            if self.process_events(mouse=True):
                self.update_board()

            # Find all the match3 groups and update the board state by
            # clearing them and then filling the board with new tiles
            # while shifting down the ones floating
            # Do this until the board state is stabilized
            groups = self.board.get_valid_groups()
            while groups:
                points = [point for group in groups for point in group]
                # Clear the tiles that create a match3 group
                self.animate_clear(points)
                self.board.clear(points)
                self.update_board()
                # Shift down the tiles that are floating and create new tiles in the top row
                # Do this until the board is filled
                board_is_not_full = True
                while board_is_not_full:
                    shifted = self.board.shift_down()
                    try:
                        shifted = shifted + self.board.populate(rows=[0, 1], no_valid_play_check=False)
                    except RecursionError:
                        print(f"Could't populate. Regenerating the board.")
                        self.board.clear()
                        try:
                            self.board.populate()
                        except RecursionError:
                            print(f"ERROR: Couldn't regenerate the the board.")
                            pygame.quit()
                            exit(1)
                        self.update_board()
                        break
                    self.animate_shift_down(shifted)
                    board_is_not_full = not self.board.is_full()

                groups = self.board.get_valid_groups()

            # Check if there is a valid play, if not, regenerate the board
            result = self.board.find_a_play()
            if len(result) == 0:
                print(f"No more moves. Regenerating the board.")
                self.board.clear()
                try:
                    self.board.populate()
                except RecursionError:
                    print(f"ERROR: Couldn't regenerate the the board.")
                    pygame.quit()
                    exit(1)
                self.update_board()
            else:
                # Let the computer play (for debug)
                (swap_points, groups) = result
                # print(f"Swapping {swap_points[0]} with {swap_points[1]}.")
                # self.animate_swap(swap_points[0], swap_points[1])
                # self.board.swap(swap_points[0], swap_points[1])
                # self.update_board()

            self.clock.tick(self.target_fps)
