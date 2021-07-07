import pygame
import random
from enum import Enum, auto
from match3_board import Match3Board


class MouseState(Enum):
    WAITING = auto()
    PRESSED = auto()
    MOVING = auto()


class Match3GUI:
    colors = [
        [128,  0,  0],  # 800000 Dark Red
        [172,172,255],  # ACACFF Light Blue
        [255,255,  0],  # FFFF00 Yellow
        [  0,128,  0],  # 008000 Green
        [ 84, 84, 84],  # 545454 Grey
        [  0,  0,128],  # 000080 Dark Blue
        [192,255,128],  # C0FF80 Pale Green-Yellow
        [ 48,192,192],  # 30C0C0 Greyed Cyan
        [192,  0,192],  # C000C0 Purple-Magenta
        [255, 64, 64],  # FF4040 Light Red
        [255,255,255],  # FFFFFF White
        [  0,  0,  0],  # 000000 Black
    ]
    border_color = (0, 0, 0)
    min_width = 500
    min_height = 500
    ani_time = 100
    target_fps = 60

    def __init__(self, side_len: int = 13) -> None:
        self.board = Match3Board(side_len, side_len, side_len-1)
        self.size = self.width, self.height = self.min_width, self.min_height
        self.circle_radius = self.width / self.board.cols / 2
        self.screen = None
        self.clock = None

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

    def animate_swap(self, point1: tuple[int, int], point2: tuple[int, int]) -> None:
        self.update_board()
        pygame.time.wait(self.ani_time)

    def animate_clear(self, points: list[tuple[int, int]]) -> None:
        self.update_board()
        pygame.time.wait(self.ani_time)

    def animate_shift_down(self) -> None:
        self.update_board()
        pygame.time.wait(self.ani_time)

    def update_board(self) -> None:
        self.clock.tick(self.target_fps)
        self.screen.fill((255, 255, 255))
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                color_index = self.board.board[row][col]
                if color_index >= 0:
                    color = self.colors[color_index]
                    pos = self.board_pos_to_win_pos(col, row)
                    pygame.draw.circle(self.screen, self.border_color, pos, int(self.circle_radius))
                    pygame.draw.circle(self.screen, color, pos, int(self.circle_radius * 9 / 10))
        pygame.display.flip()

    def run(self) -> None:
        pygame.init()
        flags = pygame.RESIZABLE
        self.screen = pygame.display.set_mode(self.size, flags, vsync=1)
        self.clock = pygame.time.Clock()

        mouse_state = MouseState.WAITING
        board_pos_src = None

        self.update_board()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.VIDEORESIZE:
                    self.width = min(event.size)
                    if self.width < self.min_width:
                        self.width = self.min_width
                    self.height = self.width
                    scale = self.width / self.size[0]
                    self.size = (self.width, self.height)
                    self.circle_radius = self.circle_radius * scale
                    self.screen = pygame.display.set_mode(self.size, flags, vsync=1)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button != 1:
                        continue
                    if mouse_state == MouseState.WAITING:
                        #print(f"MOUSEBUTTONDOWN from WAITING @ {event.pos=}")
                        board_pos_src = self.win_pos_to_board_pos(*event.pos)
                        # Check that the mouse is inside a circle
                        circle_center = self.board_pos_to_win_pos(*board_pos_src)
                        pic = self.point_inside_circle(event.pos, circle_center, int(self.circle_radius * 9 / 10))
                        if pic:
                            mouse_state = MouseState.PRESSED
                elif event.type == pygame.MOUSEMOTION:
                    if mouse_state == MouseState.PRESSED:
                        #print(f"MOUSEMOTION from PRESSED @ {event.pos=}")
                        mouse_state = MouseState.MOVING
                    if mouse_state == MouseState.MOVING:
                        #print(f"MOUSEMOTION from MOVING @ {event.pos=}")
                        board_pos_dst = self.win_pos_to_board_pos(*event.pos)
                        # Check that the mouse was dragged to a different position in the board
                        if board_pos_src == board_pos_dst:
                            continue
                        # Check that the new position is a neighbor
                        swap_valid = False
                        for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            neigh_x = board_pos_src[0] + x
                            neigh_y = board_pos_src[1] + y
                            if (neigh_x, neigh_y) == board_pos_dst:
                                swap_valid = True
                                break
                        if not swap_valid:
                            print(f"Swap not valid: destination is not a neighbor.")
                            mouse_state = MouseState.WAITING
                            continue
                        circle_center = self.board_pos_to_win_pos(*board_pos_dst)
                        pic = self.point_inside_circle(event.pos, circle_center, int(self.circle_radius * 9 / 10))
                        # Check that the mouse is inside the neighbor's circle
                        if pic:
                            # Check that the swap is valid and run the animation
                            swap_valid = self.board.is_swap_valid(board_pos_src, board_pos_dst)
                            if swap_valid:
                                # Swap is valid, do the swap in the board state
                                print(f"Swapping {board_pos_src} with {board_pos_dst}.")
                                self.board.swap(board_pos_src, board_pos_dst)
                                self.animate_swap(board_pos_src, board_pos_dst)
                            else:
                                # Swap is not valid, move back the circles to their original positions
                                print(f"Swap not valid: No match3 groups found.")
                                self.board.swap(board_pos_src, board_pos_dst)
                                self.animate_swap(board_pos_src, board_pos_dst)
                                self.board.swap(board_pos_dst, board_pos_src)
                                self.animate_swap(board_pos_dst, board_pos_src)
                            mouse_state = MouseState.WAITING
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button != 1:
                        continue
                    if mouse_state == MouseState.PRESSED:
                        #print(f"MOUSEBUTTONUP from PRESSED @ {event.pos=}")
                        mouse_state = MouseState.WAITING
                    elif mouse_state == MouseState.MOVING:
                        #print(f"MOUSEBUTTONUP from MOVING @ {event.pos=}")
                        mouse_state = MouseState.WAITING

            # Find all the match3 groups and update the board state by
            # clearing them and then filling the board with new tiles
            # while shifting down the ones floating
            # Do this until the board state is stabilized
            groups = self.board.get_valid_groups()
            while groups:
                points = [point for group in groups for point in group]
                # Clear the tiles that create a match3 group
                self.board.clear(points)
                # Run the animation to clear the tiles
                self.animate_clear(points)
                # Shift down the tiles that are floating and create new tiles in the top row
                # Do this until the board is filled
                board_is_not_full = True
                while board_is_not_full:
                    self.board.shift_down()
                    try:
                        self.board.populate(rows=[0, 1], no_valid_play_check=False)
                    except RecursionError:
                        print(f"Could't populate. Regenerating the board.")
                        print(self.board)
                        self.board.clear()
                        try:
                            self.board.populate()
                        except RecursionError:
                            print(f"ERROR: Couldn't regenerate the the board.")
                            pygame.quit()
                            return
                    board_is_not_full = not self.board.is_full()
                    # Run the animation to shift down the tiles
                    self.animate_shift_down()
                groups = self.board.get_valid_groups()

            # Check if there is a valid play, if not, regenerate the board
            result = self.board.find_a_play()
            if len(result) == 0:
                print(f"No more moves. Regenerating the board.")
                print(self.board)
                self.board.clear()
                try:
                    self.board.populate()
                except RecursionError:
                    print(f"ERROR: Couldn't regenerate the the board.")
                    pygame.quit()
                    return
            else:
                # Let the computer play (for debug)
                (swap_points, groups) = result
                print(f"Swapping {swap_points[0]} with {swap_points[1]}.")
                self.board.swap(swap_points[0], swap_points[1])
                self.animate_swap(swap_points[0], swap_points[1])
                '''if any([len(g) > 3 for g in groups]):
                    print(f"{groups=}")
                    print(self.board)
                    pygame.time.wait(5000)'''

            self.clock.tick(self.target_fps)

        pygame.quit()

        '''circle_radius = width // self.board.cols // 2
        curr_pos = [width // 2, height // 2]
        src_pos = [0, 0]
        dest_pos = [width, height]
        total_dist = [dest_pos[0] - src_pos[0], dest_pos[1] - src_pos[1]]
        ani_time = 1000
        curr_ani_time = 0
        curr_time = pygame.time.get_ticks()
        ani_time_start = curr_time

        running = True
        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    print(event.size)
                    width = min(event.size)
                    if width < 500:
                        width = 500
                    height = width
                    scale = width / size[0]
                    size = (width, height)
                    screen = pygame.display.set_mode(size, flags, vsync=1)
                    curr_pos = [int(curr_pos[0] * scale), int(curr_pos[1] * scale)]
                    src_pos = [int(src_pos[0] * scale), int(src_pos[1] * scale)]
                    dest_pos = [int(dest_pos[0] * scale), int(dest_pos[1] * scale)]
                    total_dist = [dest_pos[0] - src_pos[0], dest_pos[1] - src_pos[1]]
                    circle_radius = int(circle_radius * scale)

            screen.fill((0, 0, 0))

            curr_time = pygame.time.get_ticks()
            curr_ani_time = curr_time - ani_time_start

            partial_dist = (total_dist[0] * curr_ani_time / ani_time, total_dist[0] * curr_ani_time / ani_time)
            curr_pos = [src_pos[0] + partial_dist[0], src_pos[1] + partial_dist[1]]
            curr_pos = [int(curr_pos[0]), int(curr_pos[1])]
            for i in range(2):
                dir = dest_pos[i] - src_pos[i]
                if (dir < 0 and curr_pos[i] < dest_pos[i]) or (dir > 0 and curr_pos[i] > dest_pos[i]):
                    curr_pos[i] = dest_pos[i]

            if curr_pos == dest_pos:
                curr_ani_time = 0
                ani_time_start = curr_time
                tmp_pos = src_pos
                src_pos = dest_pos
                dest_pos = tmp_pos
                total_dist = [dest_pos[0] - src_pos[0], dest_pos[1] - src_pos[1]]
                print(clock.get_fps())

            pygame.draw.circle(screen, (255, 255, 255), curr_pos, circle_radius)

            pygame.display.flip()'''
