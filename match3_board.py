import copy
import random

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
        return result

    def clear(self, points: list[tuple[int, int]] = None) -> None:
        if points is None:
            self.board = [[self.empty for _ in range(self.cols)] for _ in range(self.rows)]
        else:
            for (x, y) in points:
                self.board[y][x] = self.empty

    def populate(self, cols: tuple[int, int] = None, rows: tuple[int, int] = None, no_valid_play_check: bool = True) -> int:
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
                        return self.populate(cols, rows, no_valid_play_check)
        # Check that the board has at least one possible play, if not, re-run.
        if no_valid_play_check and len(self.find_a_play()) == 0:
            self.board = backup_board
            return self.populate(cols, rows, no_valid_play_check)
        return empty_count

    def out_of_bounds(self, col: int, row: int) -> bool:
        return col < 0 or row < 0 or col >= self.cols or row >= self.rows

    def get_group(self, col: int, row: int, group: list[tuple[int, int]] = None) -> list[tuple[int, int]]:
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
        return group

    def are_elems_contiguous(self, l: list[int]) -> bool:
        l.sort()
        for i in range(1, len(l)):
            if l[i] - l[i-1] != 1:
                return False
        return True

    def filter_group(self, group: list[tuple[int, int]]) -> list[tuple[int, int]]:
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
        return filtered_group

    def swap(self, point1: tuple[int, int], point2: tuple[int, int]) -> None:
        (x1, y1), (x2, y2) = point1, point2
        tmp = self.board[y1][x1]
        self.board[y1][x1] = self.board[y2][x2]
        self.board[y2][x2] = tmp

    def find_a_play(self) -> tuple[tuple[tuple[int, int], tuple[int, int]], list[list[tuple[int, int]]]]:
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
                    self.swap(*swap_points)
                    if len(groups) > 0:
                        return (swap_points, groups)
        return tuple()

    def shift_down(self) -> None:
        for row in reversed(range(0, self.rows - 1)):
            for col in reversed(range(0, self.cols)):
                if self.board[row + 1][col] == self.empty:
                    self.swap((col, row), (col, row + 1))

    def get_valid_groups(self) -> list[list[tuple[int, int]]]:
        groups = list()
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] == self.empty:
                    continue
                group = list(self.filter_group(self.get_group(col, row)))
                if len(group) > 0:
                    group.sort(key=lambda l: l[1])
                    group.sort(key=lambda l: l[0])
                    if group not in groups:
                        groups.append(group)
        return groups

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
