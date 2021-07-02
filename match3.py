import copy
import random
import time

class Match3Board:
    def __init__(self, cols: int = 5, rows: int = 5, values: set[str] = {'B', 'W'}) -> None:
        if cols < 3 or rows < 3:
            raise ValueError("Board minimum size is 3x3.")
        if cols > 100 or rows > 100:
            raise ValueError("Board maximum size is 100x100.")
        if len(values) < 2:
            raise ValueError("Board must have at least two values.")
        if len(values)**2 >= cols * rows:
             raise ValueError("Number of values must be less than the square root of the board area.")
        self.cols = cols
        self.rows = rows
        self.values = values
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
                result += f"{self.board[row][col]:>3}"
            if row != self.rows - 1:
                result += "\n"
        result += "\n"
        return result

    def __repr__(self) -> str:
        return str(self.board)

    def clear(self, points: list[tuple[int, int]] = None) -> None:
        if points is None:
            self.board = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
        else:
            for (x, y) in points:
                self.board[y][x] = ' '

    def populate(self) -> None:
        backup_board = copy.deepcopy(self.board)
        for row in range(self.rows):
            for col in range(self.cols):
                # If the current space is empty, place a new random value.
                if self.board[row][col] not in self.values:
                    values_left = copy.deepcopy(self.values)
                    while len(values_left):
                        value = random.choice(list(values_left))
                        values_left.remove(value)
                        self.board[row][col] = value
                        # Check that placing the new random value doesn't result in a match3 group.
                        if not self.filter_group(self.get_group(col, row)):
                            break
                    # If after checking all possible values no value was found that didn't result in a match3 group, re-run.
                    if not len(values_left):
                        self.board = backup_board
                        self.populate()
                        return
        # Check that the board has at least one possible play, if not, re-run.
        if len(self.find_a_play()) == 0:
            self.board = backup_board
            self.populate()

    def out_of_bounds(self, col: int, row: int) -> bool:
        return col < 0 or row < 0 or col > len(self.board[0]) - 1 or row > len(self.board) - 1

    def get_group(self, col: int, row: int, group: set[tuple[int, int]] = None) -> set[tuple[int, int]]:
        if group is None:
            group = set()
        for (offset_x, offset_y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neigh_x = col + offset_x
            neigh_y = row + offset_y
            if self.out_of_bounds(neigh_x, neigh_y):
                continue
            if self.board[row][col] == self.board[neigh_y][neigh_x] and (neigh_x, neigh_y) not in group:
                group.add((neigh_x, neigh_y))
                group = self.get_group(neigh_x, neigh_y, group)
        return group

    def are_elems_contiguous(self, l: list[int]) -> bool:
        l.sort()
        for i in range(1, len(l)):
            if l[i] - l[i-1] != 1:
                return False
        return True

    def filter_group(self, group: set[tuple[int, int]]) -> set[tuple[int, int]]:
        points_in_line = dict()
        for (col, row) in group:
            points_in_line[f"x={col}"] = points_in_line.get(f"x={col}", list()) + [(col, row)]
            points_in_line[f"y={row}"] = points_in_line.get(f"y={row}", list()) + [(col, row)]
        filtered_group = set()
        for line, points in points_in_line.items():
            if len(points) >= 3:
                # Check that only groups of 3 contiguous elements are valid.
                dim = {'x': 1, 'y': 0}[line[0]]
                if self.are_elems_contiguous([point[dim] for point in points]):
                    filtered_group.update(points)
        return filtered_group

    def swap(self, point1: tuple[int, int], point2: tuple[int, int]) -> None:
        (x1, y1), (x2, y2) = point1, point2
        tmp = self.board[y1][x1]
        self.board[y1][x1] = self.board[y2][x2]
        self.board[y2][x2] = tmp

    def find_a_play(self) -> tuple[tuple[tuple[int, int], tuple[int, int]], tuple[set[tuple[int, int]], ...]]:
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
                        if group:
                            groups.append(group)
                    groups = tuple(groups)
                    self.swap(*swap_points)
                    if groups:
                        return (swap_points, groups)
        return tuple()


def test() -> None:
    last_num_values_found = 2
    for rows in range(3, 11):
        for cols in range(3, 11):
            values = ['a', 'b']
            swap = None
            while len(values)**2 < cols*rows:
                if len(values) >= last_num_values_found:
                    attempts_max = 1000
                    while attempts_max:
                        board = Match3Board(cols, rows, set(values))
                        swap = board.find_a_play()
                        if len(swap) == 0:
                            print(f"swap NOT found | {rows=} {cols=} area={cols*rows} num_values={len(values)}")
                            last_num_values_found = len(values) - 1
                            break
                        attempts_max -= 1
                    if attempts_max <= 0:
                        print(f"swap found | {rows=} {cols=} area={cols*rows} num_values={len(values)}")
                values.append(chr(ord(values[-1]) + 1))
                if swap is not None and len(swap) == 0:
                    break


if __name__ == "__main__":
    # test()

    values = set([chr(ord('a') + i) for i in range(6)])
    board = Match3Board(7, 7, values)
    sleep_time = 1
    while True:
        do_print = False
        # Find a valid play
        (swap_points, groups) = board.find_a_play()
        # Activate print only when a match3 group with size >= X is found
        if max([len(g) for g in groups]) >= 3:
            # print(swap_points)
            # print(groups)
            do_print = True
        # Print current board state
        if do_print:
            time.sleep(sleep_time)
            print(board)
        # Do the play
        board.swap(*swap_points)
        # Print board state after the swap
        if do_print:
            time.sleep(sleep_time)
            print(board)
        # Clear the tiles that create a match3 group
        board.clear([point for group in groups for point in group])
        # Print board state with the cleared tiles
        if do_print:
            time.sleep(sleep_time)
            print(board)
        # Fill the cleared tiles with new random values
        board.populate()

# TODO: do the shift down + generate + clear for extra points instead of repopulating in place
