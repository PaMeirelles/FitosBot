from Board import Board
from constants import NEIGHBOURS

POS_GAPS = [0, 1, 2, 1, 0,
            1, 2, 3, 2, 1,
            2, 3, 4, 3, 2,
            1, 2, 3, 2, 1,
            0, 1, 2, 1, 2]

class Parameters:
    def __init__(self, centrality_gap, h2_gap, sh1, sh2, nh1, nh2, ph1, ph2, nn1, nn2):
        self.posScore = [centrality_gap * x for x in POS_GAPS]
        self.heightScore = [0, 100, h2_gap + 100, h2_gap + 50]
        self.sameHeightSupport = [0, sh1, sh1 + sh2]
        self.nextHeightSupport = [0, nh1, nh1 + nh2]
        self.prevHeightSupport = [0, ph2, ph1 + ph2]  # <- inverted scoring here
        self.nextNextHeightSupport = [0, nn2, nn1 + nn2]

PARAMS = Parameters(
    centrality_gap=20,
    h2_gap=250,
    sh1=60, sh2=30,
    nh1=80, nh2=40,
    ph1=20, ph2=10,
    nn1=25, nn2=15,
)

TEMPO = 50

def score_position(b: Board, parameters: Parameters = PARAMS) -> int:
    def score_worker(worker_pos: int) -> int:
        square = b.workers[worker_pos]
        height = b.blocks[square]

        p_score = parameters.posScore[square]
        h_score = parameters.heightScore[height]

        same_h = 0
        next_h = 0
        next_next_h = 0
        prev_h = 0

        for n in NEIGHBOURS[square]:
            if b.is_free(n):
                h = b.blocks[n]
                if h == height:
                    same_h += 1
                elif h == height + 1:
                    next_h += 1
                elif h == height - 1:
                    prev_h += 1
                elif h == height + 2:
                    next_next_h += 1

        same_h = min(same_h, 2)
        next_h = min(next_h, 2)

        if height != 0:
            if same_h == 0:
                prev_h = min(prev_h, 2)
            elif same_h == 1:
                prev_h = 1 if prev_h >= 1 else 0  # Will score as second-tier now
            else:
                prev_h = 0
        else:
            prev_h = 0
            same_h = 0

        if height < 2:
            if next_h == 0:
                next_next_h =min(next_next_h, 2)
            elif next_h == 1:
                next_next_h = 1 if next_next_h >= 1 else 0
            else:
                next_next_h = 0
        else:
            next_next_h = 0

        support = (
            parameters.sameHeightSupport[same_h]
            + parameters.nextHeightSupport[next_h]
            + parameters.prevHeightSupport[prev_h]
            + parameters.nextNextHeightSupport[next_next_h]
        )

        return p_score + h_score + support
    tempo_score = TEMPO if b.turn == 1 else 0
    return score_worker(0) + score_worker(1) - score_worker(2) - score_worker(3) + tempo_score
