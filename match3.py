import sys
from match3_gui import Match3GUI


if __name__ == "__main__":
    side_len = 7
    if len(sys.argv) > 1:
        try:
            side_len = int(sys.argv[1])
        except ValueError:
            print(f"ERROR: Argument is not an int.")
            exit(1)
    gui = Match3GUI(side_len)
    gui.run()
