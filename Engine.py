from Board import Board
from search import get_best_move


class SantoriniEngine:
    def __init__(self):
        self.board = None

    def run(self):
        while True:
            try:
                line = input()
            except EOFError:
                break

            if not line.strip():
                continue

            if line.startswith("isready"):
                print("readyok")

            elif line.startswith("position"):
                # Position command: e.g. "position <position_string>"
                tokens = line.split(maxsplit=1)
                if len(tokens) < 2:
                    print("Error: Missing position argument.")
                    continue

                position_str = tokens[1]
                self.board = Board(position_str)
                print("Position set.")

            elif line.startswith("go"):
                # Example: "go gtime 5000 btime 3000"
                if self.board is None:
                    print("bestmove none")
                    continue

                # Default times if user doesn't specify
                gtime = 1000
                btime = 1000

                tokens = line.split()
                for i, token in enumerate(tokens):
                    if token == "gtime":
                        gtime = int(tokens[i+1])
                    elif token == "btime":
                        btime = int(tokens[i+1])

                # Gray = turn == 1, Blue = turn == -1
                remaining_time_ms = gtime if self.board.turn == 1 else btime

                # Call get_best_move with correct arguments
                move = get_best_move(self.board, remaining_time_ms)
                if not move:
                    print("bestmove none")
                else:
                    print(f"bestmove {move.to_text()}")

            elif line.startswith("quit"):
                break

            else:
                print(f"Unknown command: {line}")



if __name__ == "__main__":
    engine = SantoriniEngine()
    engine.run()
