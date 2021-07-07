import pygame
import random
from match3_board import Match3Board


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

    def __init__(self) -> None:
        size = 13
        self.board = Match3Board(size, size, size-1)
        self.min_width = 500
        self.min_height = 500

    def run(self) -> None:
        pygame.init()
        size = width, height = self.min_width, self.min_height
        flags = pygame.RESIZABLE
        screen = pygame.display.set_mode(size, flags, vsync=1)
        clock = pygame.time.Clock()

        circle_radius = width / self.board.cols / 2

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    width = min(event.size)
                    if width < self.min_width:
                        width = self.min_width
                    height = width
                    scale = width / size[0]
                    size = (width, height)
                    circle_radius = circle_radius * scale
                    screen = pygame.display.set_mode(size, flags, vsync=1)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button != 1:
                        continue
                    print(f"{event.pos=}")
                    print(f"{event.button=}")
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button != 1:
                        continue
                    print(f"{event.pos=}")
                    print(f"{event.button=}")

            clock.tick(60)
            screen.fill((255, 255, 255))

            col_w = width / self.board.cols
            row_h = height / self.board.rows
            border_color = [0, 0, 0] if random.randint(0, 1) == 0 else [255,255,255]
            for row in range(self.board.rows):
                for col in range(self.board.cols):
                    ci = self.board.board[row][col]
                    color = self.colors[ci]
                    pos = (int(col * col_w + col_w / 2), int(row * row_h + row_h / 2))
                    if border_color == [0,0,0]:
                        border_color = [255,255,255]
                    else:
                        border_color = [0,0,0]
                    pygame.draw.circle(screen, border_color, pos, int(circle_radius))
                    pygame.draw.circle(screen, color, pos, int(circle_radius * 9 / 10))

            pygame.display.flip()

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
