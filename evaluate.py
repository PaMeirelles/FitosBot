from Board import Board
from constants import NEIGHBOURS

posScore = [-50, -30, -10, -30, -50,
            -30,  10,  30,  10, -30,
            -10,  30,  50,  30,  10,
            -30,  10,  30,  10, -30,
            -50, -30, -10, -30, -50]

h1 = 100
h2_gap = 300   # h2 = h1 + h2_gap
h3_gap = -50   # h3 = h2 + h3_gap
heightScore = [0, h1, h1 + h2_gap, h1 + h2_gap + h3_gap]

sameHeightSupport = [-30, 0, 55]
nextHeightSupport = [0, 35, 120]

def score_position(b: Board) -> int:

    def score_worker(worker_pos: int) -> int:
        square = b.workers[worker_pos]
        height = b.blocks[square]

        p_score = posScore[square]
        h_score = heightScore[height]

        support = 0

        if height > 0:
            same_h = 0
            next_h = 0
            for n in NEIGHBOURS[square]:
                if b.is_free(n):
                    if b.blocks[n] == height:
                        same_h += 1
                    elif b.blocks[n] == height + 1:
                        next_h += 1

            same_h = min(same_h, 2)
            next_h = min(next_h, 2)
            support = sameHeightSupport[same_h] + nextHeightSupport[next_h]

        return p_score + h_score + support

    return score_worker(0) + score_worker(1) - score_worker(2) - score_worker(3)


if __name__ == '__main__':
    b = Board("2G2N0N0N2N0N4N0N1N2B0N1B0G0N2N0N0N0N0N0N0N0N0N0N0N1500")
    print(score_position(b))