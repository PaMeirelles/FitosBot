import random
from Board import Board

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

                move = self.get_best_move()
                if not move: print("bestmove none")
                print(f"bestmove {move.to_text()}")
            elif line.startswith("quit"):
                break
            else:
                print(f"Unknown command: {line}")

    def get_best_move(self):
        moves = self.board.get_moves()
        scored_moves = []
        for move in moves:
            self.board.make_move(move)
            score = self.board.check_state()
            self.board.unmake_move(move)
            scored_moves.append((score, move))
        sorted_scored_moves = sorted(scored_moves, key=lambda x: x[0])
        return sorted_scored_moves[0][1]

if __name__ == "__main__":
    engine = SantoriniEngine()
    engine.run()