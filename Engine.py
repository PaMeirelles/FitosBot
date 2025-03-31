import random
import sys
from Board import Board
from Move import Move

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
                self.board = Board(line.split(" ")[1])
                print("Position set.")
            elif line.startswith("go"):
                if self.board is None:
                    print("bestmove none")
                    continue

                moves = self.board.generate_moves()
                if not moves:
                    print("bestmove none")
                    continue

                move = random.choice(moves)
                print(f"bestmove {move.to_text()}")
            elif line.startswith("quit"):
                break
            else:
                print(f"Unknown command: {line}")

if __name__ == "__main__":
    engine = SantoriniEngine()
    engine.run()