from Board import Board
from constants import NEIGHBOURS

POS_GAPS = [0, 1, 2, 1, 0,
            1, 2, 3, 2, 1,
            2, 3, 4, 3, 2,
            1, 2, 3, 2, 1,
            0, 1, 2, 1, 2]

class Parameters:
    def __init__(self, centrality_gap, h2_gap, sh1, sh2, nh1, nh2):
        self.posScore = [centrality_gap * x for x in POS_GAPS]
        self.heightScore = [0, 100, h2_gap + 100, h2_gap + 50]
        self.sameHeightSupport = [0, sh1, sh1 + sh2]
        self.nextHeightSupport = [0, nh1, nh1 + nh2]

PARAMS = Parameters(25, 260, 70, 25, 90, 40)


def score_position(b: Board, parameters:Parameters=PARAMS) -> int:
    def score_worker(worker_pos: int) -> int:
        square = b.workers[worker_pos]
        height = b.blocks[square]

        p_score = parameters.posScore[square]
        h_score = parameters.heightScore[height]

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
        if height != 0:
            shs = parameters.sameHeightSupport[same_h]
        else:
            shs = 0

        support = shs + parameters.nextHeightSupport[next_h]

        return p_score + h_score + support

    return score_worker(0) + score_worker(1) - score_worker(2) - score_worker(3)


if __name__ == '__main__':
    board = Board("2G2N0N0N2N0N4N0N1N2B0N1B0G0N2N0N0N0N0N0N0N0N0N0N0N1500")
    default_parameters = Parameters(20, 300, 30, 55, 35, 85)
    print(score_position(board, default_parameters))