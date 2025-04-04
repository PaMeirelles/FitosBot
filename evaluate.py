from Board import Board

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


def score_position(board: Board) -> int:
    """
    Returns an integer evaluation of the position from Gray's point of view:
      + higher = better for Gray
      + lower  = better for Blue
    """

    # Check if there's a winner:
    state = board.check_state()
    if state == 1:
        return 999999  # Gray has won
    if state == -1:
        return -999999  # Blue has won

    # Otherwise, sum up each side’s position scores and height bonuses
    score = 0
    gray_workers = [board.workers[0], board.workers[1]]
    blue_workers = [board.workers[2], board.workers[3]]

    for sq in gray_workers:
        h = board.blocks[sq]
        if h >= 3:
            h = 2
        score += posScore[sq] + heightScore[h]

    for sq in blue_workers:
        h = board.blocks[sq]
        if h >= 3:
            h = 2
        score -= (posScore[sq] + heightScore[h])

    return score