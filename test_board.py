import time
from match3_board import Match3Board


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
