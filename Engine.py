import random
from Board import Board

# ---------------------------
# 1) Define the scoring arrays
# ---------------------------
posScore = [
   -50, -30, -10, -30, -50,
   -30,  10,  30,  10, -30,
   -10,  30,  50,  30,  10,
   -30,  10,  30,  10, -30,
   -50, -30, -10, -30, -50
]

# heightScore[i] is the bonus if a worker is on height i, for i = 0..2.
# If a worker stands on height 3, that typically is an instant win.
heightScore = [0, 100, 400]


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
                if not move:
                    print("bestmove none")
                else:
                    print(f"bestmove {move.to_text()}")

            elif line.startswith("quit"):
                break

            else:
                print(f"Unknown command: {line}")

    # -------------------------------------------------------------
    # 2) Our improved "get_best_move" that uses the new scoring
    # -------------------------------------------------------------
    def get_best_move(self):
        moves = self.board.generate_moves()
        if not moves:
            return None

        best_moves = []
        best_score = -999999 if self.board.turn == 1 else 999999

        for move in moves:
            self.board.make_move(move)
            score = self.score_position()
            self.board.unmake_move(move)

            if self.board.turn == 1:
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            else:
                if score < best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)

        return random.choice(best_moves)

    # -------------------------------------------------------------
    # 3) Score the board using posScore + heightScore
    # -------------------------------------------------------------
    def score_position(self) -> int:
        """
        Returns an integer evaluation of the position from Gray's point of view:
          + higher = better for Gray
          + lower  = better for Blue
        """

        # First, check if there's a winner:
        state = self.board.check_state()
        if state == 1:
            # Gray just won
            return 999999
        if state == -1:
            # Blue just won
            return -999999

        # Otherwise, sum up each side’s position scores and height bonuses
        score = 0

        # workers[0..1] = Gray's workers, [2..3] = Blue's
        gray_workers = [self.board.workers[0], self.board.workers[1]]
        blue_workers = [self.board.workers[2], self.board.workers[3]]

        # --- Sum over Gray's workers
        for sq in gray_workers:
            h = self.board.blocks[sq]
            # If h >= 3, they've effectively reached top or near-win – you could
            # clamp to 2 or handle specially. We'll just clamp to 2 here:
            if h >= 3:
                h = 2
            score += posScore[sq] + heightScore[h]

        # --- Subtract Blue's workers
        for sq in blue_workers:
            h = self.board.blocks[sq]
            if h >= 3:
                h = 2
            score -= (posScore[sq] + heightScore[h])

        return score


if __name__ == "__main__":
    engine = SantoriniEngine()
    engine.run()
