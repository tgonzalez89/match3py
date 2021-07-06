import copy
import random
import time

class Match3Board:
    empty = ord(' ') - ord('a')

    def __init__(self, cols: int = 5, rows: int = 5, num_values: int = 4) -> None:
        if cols < 3 or rows < 3:
            raise ValueError("Minimum size is 3x3.")
        if cols > 27 or rows > 27:
            raise ValueError("Maximum size is 27x27.")
        if num_values < 2:
            raise ValueError("Number of values must be at least 2.")
        if num_values**2 >= cols * rows:
             raise ValueError("Number of values must be less than the square root of the board area.")
        self.cols = cols
        self.rows = rows
        self.values = tuple([i for i in range(num_values)])
        self.board = None
        self.clear()
        self.populate()

    def __str__(self) -> str:
        result = "  "
        for col in range(self.cols):
            result += f"{col:>3}"
        result += "\n"
        for row in range(self.rows):
            result += f"{row:>2}"
            for col in range(self.cols):
                result += f"{chr(self.board[row][col] + ord('a')):>3}"
            if row != self.rows - 1:
                result += "\n"
        result += "\n"
        return result

    def clear(self, points: list[tuple[int, int]] = None) -> None:
        if points is None:
            self.board = [[self.empty for _ in range(self.cols)] for _ in range(self.rows)]
        else:
            for (x, y) in points:
                self.board[y][x] = self.empty

    def populate(self, cols: tuple[int, int] = None, rows: tuple[int, int] = None) -> int:
        if cols is None:
            cols = (0, self.cols)
        if rows is None:
            rows = (0, self.rows)
        backup_board = copy.deepcopy(self.board)
        empty_count = 0
        for row in range(rows[0], rows[1]):
            for col in range(cols[0], cols[1]):
                # If the current space is empty, place a new random value.
                if self.board[row][col] == self.empty:
                    empty_count += 1
                    values_left = list(self.values)
                    while len(values_left):
                        value = random.choice(values_left)
                        values_left.remove(value)
                        self.board[row][col] = value
                        # Check that placing the new random value doesn't result in a match3 group.
                        if not self.filter_group(self.get_group(col, row)):
                            break
                    # If after checking all possible values no value was found that didn't result in a match3 group, re-run.
                    if not len(values_left):
                        self.board = backup_board
                        return self.populate(cols, rows)
        # Check that the board has at least one possible play, if not, re-run.
        if len(self.find_a_play()) == 0:
            self.board = backup_board
            return self.populate(cols, rows)
        return empty_count

    def out_of_bounds(self, col: int, row: int) -> bool:
        return col < 0 or row < 0 or col >= self.cols or row >= self.rows

    def get_group(self, col: int, row: int, group: tuple[tuple[int, int], ...] = None) -> tuple[tuple[int, int], ...]:
        if group is None:
            group = list()
        for (offset_x, offset_y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neigh_x = col + offset_x
            neigh_y = row + offset_y
            if self.out_of_bounds(neigh_x, neigh_y):
                continue
            if self.board[row][col] != self.board[neigh_y][neigh_x]:
                continue
            if (neigh_x, neigh_y) in group:
                continue
            group.append((neigh_x, neigh_y))
            group = list(self.get_group(neigh_x, neigh_y, group))
        return tuple(group)

    def are_elems_contiguous(self, l: list[int]) -> bool:
        l.sort()
        for i in range(1, len(l)):
            if l[i] - l[i-1] != 1:
                return False
        return True

    def filter_group(self, group: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
        points_in_line = dict()
        for (col, row) in group:
            points_in_line[f"x={col}"] = points_in_line.get(f"x={col}", list()) + [(col, row)]
            points_in_line[f"y={row}"] = points_in_line.get(f"y={row}", list()) + [(col, row)]
        filtered_group = list()
        for line, points in points_in_line.items():
            if len(points) >= 3:
                # Check that only groups of 3 contiguous elements are valid.
                dim = {'x': 1, 'y': 0}[line[0]]
                if self.are_elems_contiguous([point[dim] for point in points]):
                    for point in points:
                        if point not in filtered_group:
                            filtered_group.append(point)
        return tuple(filtered_group)

    def swap(self, point1: tuple[int, int], point2: tuple[int, int]) -> None:
        (x1, y1), (x2, y2) = point1, point2
        tmp = self.board[y1][x1]
        self.board[y1][x1] = self.board[y2][x2]
        self.board[y2][x2] = tmp

    def find_a_play(self) -> tuple[tuple[tuple[int, int], tuple[int, int]], tuple[tuple[tuple[int, int], ...], ...]]:
        for row in range(self.rows):
            for col in range(self.cols):
                for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neigh_x = col + x
                    neigh_y = row + y
                    if self.out_of_bounds(neigh_x, neigh_y) or self.board[row][col] == self.board[neigh_y][neigh_x]:
                        continue
                    swap_points = ((col, row), (neigh_x, neigh_y))
                    self.swap(*swap_points)
                    groups = list()
                    for (x, y) in swap_points:
                        group = self.filter_group(self.get_group(x, y))
                        if len(group) > 0:
                            groups.append(group)
                    groups = tuple(groups)
                    self.swap(*swap_points)
                    if len(groups) > 0:
                        return (swap_points, groups)
        return tuple()

    def shift_down(self) -> None:
        for row in reversed(range(0, self.rows - 1)):
            for col in reversed(range(0, self.cols)):
                if self.board[row + 1][col] == self.empty:
                    self.swap((col, row), (col, row + 1))

    def get_valid_groups(self) -> tuple[tuple[tuple[int, int], ...], ...]:
        groups = list()
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] == self.empty:
                    continue
                group = list(self.filter_group(self.get_group(col, row)))
                if len(group) > 0:
                    group.sort(key=lambda l: l[1])
                    group.sort(key=lambda l: l[0])
                    group = tuple(group)
                    if group not in groups:
                        groups.append(group)
        return tuple(groups)

    def is_full(self) -> bool:
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] == self.empty:
                    return False
        return True

    def is_swap_valid(self, point1: tuple[int, int], point2: tuple[int, int]) -> bool:
        if self.out_of_bounds(*point1) or self.out_of_bounds(*point2):
            return False
        self.swap(point1, point2)
        groups = list()
        for (x, y) in (point1, point2):
            group = self.filter_group(self.get_group(x, y))
            if len(group) > 0:
                groups.append(group)
        self.swap(point1, point2)
        return len(groups) > 0


def test() -> None:
    last_num_values_found = 2
    for rows in range(3, 11):
        for cols in range(3, 11):
            num_values = 2
            swap = None
            while num_values**2 < cols*rows:
                if num_values >= last_num_values_found:
                    attempts_max = 1000
                    while attempts_max:
                        board = Match3Board(cols, rows, num_values)
                        swap = board.find_a_play()
                        if len(swap) == 0:
                            print(f"swap NOT found | {rows=} {cols=} area={cols*rows} num_values={num_values}")
                            last_num_values_found = num_values - 1
                            break
                        attempts_max -= 1
                    if attempts_max <= 0:
                        print(f"swap found | {rows=} {cols=} area={cols*rows} num_values={num_values}")
                num_values += 1
                if swap is not None and len(swap) == 0:
                    break


def is_int(s: str) -> int:
    try: 
        int(s)
        return True
    except Exception:
        return False


def get_user_input() -> tuple[tuple[int, int], tuple[int, int]]:
    input_str = input("Type your play (x y dir): ")
    input_list = input_str.split()
    if len(input_list) != 3:
        return None
    if not (is_int(input_list[0]) and is_int(input_list[1])):
        return None
    x, y = int(input_list[0]), int(input_list[1])
    if input_list[2] == 'u':
        swap_points = ((x, y), (x, y - 1))
    elif input_list[2] == 'd':
        swap_points = ((x, y), (x, y + 1))
    elif input_list[2] == 'l':
        swap_points = ((x, y), (x - 1, y))
    elif input_list[2] == 'r':
        swap_points = ((x, y), (x + 1, y))
    else:
        return None
    return swap_points


if __name__ == "__main__":
    # test()

    board = Match3Board(7, 7, 6)
    sleep_time = 1
    # Print initial board state
    print(board)
    while True:
        do_print = True
        # Find a valid play
        (swap_points, groups) = board.find_a_play()
        print(f"{swap_points=}")
        time.sleep(3)
        '''# Activate print only when a match3 group with size >= X is found
        if max([len(g) for g in groups]) >= 3:
            do_print = True'''
        # Wait for the user input
        # swap_points = get_user_input()
        if swap_points is None:
            print("Bad input.")
            continue
        # Check that play is valid
        if not board.is_swap_valid(*swap_points):
            print("Play is not valid.")
            continue
        # Do the play
        board.swap(*swap_points)
        # Print board state after the swap
        # print(f"{swap_points=}")
        if do_print:
            time.sleep(sleep_time)
            print(board)
        # Find all the match3 groups and print the board state
        # Then fill the board with new tiles while shifting down the ones floating
        # Do this until the board state is stabilized
        groups = board.get_valid_groups()
        while groups:
            # print(f"{groups=}")
            # Clear the tiles that create a match3 group
            board.clear([point for group in groups for point in group])
            # Print board state with the cleared tiles
            if do_print:
                time.sleep(sleep_time)
                print(board)
            # Shift down the tiles that are floating and create new tiles in the top row
            # Do this until the board is filled
            board_is_not_full = True
            while board_is_not_full:
                board.shift_down()
                board.populate(rows=[0, 1])
                board_is_not_full = not board.is_full()
                # print(f"{board_is_not_full=}")
                # Print board state with shifted down tiles and the generated new tiles
                if do_print:
                    time.sleep(sleep_time)
                    print(board)
            groups = board.get_valid_groups()
