from match3_board import Match3Board


def run() -> None:
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


if __name__ == "__main__":
    run()
