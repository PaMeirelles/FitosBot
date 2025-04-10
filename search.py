import time
from math import floor
from typing import Optional, List

from Board import Board
from Move import Move
from board_tests import make_position
from constants import DOUBLE_NEIGHBORS, God
from evaluate import score_position
from transposition_table import TranspositionTable


MATE: int = 10000
CHECK_EVERY: int = 4096  # how often we check for time in the search
WIN: int = 9999

def is_mate(score: int) -> bool:
    return score > (MATE - 100) or score < (-MATE + 100)

class SearchInfo:
    def __init__(self, board: Board, depth: int, end_time: float) -> None:
        self.board: Board = board            # Board reference
        self.depth: int = depth            # Current search depth
        self.nodes: int = 0                # Node counter
        self.quit: bool = False            # Set to True if time runs out
        self.end_time: float = end_time    # Time (in seconds) when we must stop
        self.bestMove: Optional[Move] = None  # Will store the best move found at this depth


def evaluate(board: Board) -> int:
    return score_position(board) * board.turn

def score_moves(moves: List[Move], board: Board) -> None:
    for mv in moves:
        from_h: int = board.blocks[mv.from_sq]
        to_h: int = board.blocks[mv.final_sq]
        mv.score = (to_h - from_h) * 10 + (DOUBLE_NEIGHBORS[mv.final_sq] - DOUBLE_NEIGHBORS[mv.from_sq])

def pick_move(moves: List[Move], start_index: int) -> None:
    best_idx: int = start_index
    best_score: int = moves[best_idx].score
    for i in range(start_index + 1, len(moves)):
        if moves[i].score > best_score:
            best_idx = i
            best_score = moves[i].score
    if best_idx != start_index:
        moves[start_index], moves[best_idx] = moves[best_idx], moves[start_index]


def qsearch(search_info: SearchInfo, alpha: int, beta: int) -> int:
    search_info.nodes += 1

    if (search_info.nodes % CHECK_EVERY) == 0 and time.time() > search_info.end_time:
        search_info.quit = True
        return 0

    state = search_info.board.check_state()
    if state != 0:
        return MATE - 1 if state == search_info.board.turn else -MATE + 1

    stand_pat = evaluate(search_info.board)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    for move in search_info.board.generate_moves():
        from_h = search_info.board.blocks[move.from_sq]
        to_h = search_info.board.blocks[move.final_sq]

        # Allow climbs or Pan drop-wins only
        god_index = 0 if search_info.board.turn == 1 else 1
        god = search_info.board.gods[god_index]

        is_climb = to_h > from_h
        is_pan_drop = (
            god == God.PAN and from_h - to_h >= 2
        )

        if not (is_climb or is_pan_drop):
            continue

        search_info.board.make_move(move)
        score = -qsearch(search_info, -beta, -alpha)
        search_info.board.unmake_move(move)

        if search_info.quit:
            return 0

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha



def search(search_info: SearchInfo, depth: int, ply: int, alpha: int, beta: int, tt: TranspositionTable) -> int:
    search_info.nodes += 1

    # Check time every CHECK_EVERY nodes.
    if (search_info.nodes % CHECK_EVERY) == 0:
        if time.time() > search_info.end_time:
            search_info.quit = True
            search_info.bestMove = None
            return 0

    state: int = search_info.board.check_state()
    if state != 0:
        # Terminal state: adjust mate score by ply.
        if state == search_info.board.turn:
            # Win: faster mate (smaller ply) gives a higher score.
            return MATE - ply
        else:
            # Loss: delaying mate (larger ply) is better.
            return -MATE + ply

    # Leaf node: return static evaluation.
    if depth == 0:
        return qsearch(search_info, alpha, beta)

    # Probe the transposition table.
    tt_move, tt_score = tt.probe(search_info.board, alpha, beta, depth)
    if tt_move is not None:
        return tt_score

    moves: List[Move] = search_info.board.generate_moves()
    if not moves:
        return -MATE + ply  # No moves: mate is inevitable.

    max_score: int = -MATE * 100
    best_move: Optional[Move] = None
    original_alpha = alpha

    score_moves(moves, search_info.board)

    for i in range(len(moves)):
        pick_move(moves, i)
        move = moves[i]

        search_info.board.make_move(move)
        curr_score = -search(search_info, depth - 1, ply + 1, -beta, -alpha, tt)
        search_info.board.unmake_move(move)

        if curr_score > max_score:
            max_score = curr_score
            best_move = move
            if max_score > alpha:
                if max_score >= beta:
                    search_info.bestMove = best_move
                    tt.store(search_info.board, best_move, beta, depth, 'B')
                    return beta
                alpha = max_score

        if search_info.quit:
            search_info.bestMove = None
            return 0

    search_info.bestMove = best_move
    if alpha != original_alpha:
        tt.store(search_info.board, best_move, max_score, depth, 'E')
    else:
        tt.store(search_info.board, best_move, alpha, depth, 'A')

    return alpha


def get_best_move(board: Board, remaining_time_ms: int, tt: TranspositionTable, max_depth: Optional[int] = None) -> Optional[Move]:
    """
    Use iterative deepening to find the best move.
    """
    thinking_time: int = floor(remaining_time_ms / 10)
    start_time: float = time.time()
    end_time: float = start_time + (thinking_time / 1000.0)
    best_move = None
    best_score = None
    depth: int = 1
    while True:
        search_info = SearchInfo(board, depth, end_time)
        # Start the ply counter at 0.
        search(search_info, depth, 0, -MATE, MATE, tt)
        candidate_best_move, candidate_best_score = tt.probe_pv_move(board)
        if candidate_best_move is not None:
            best_move = candidate_best_move
            best_score = candidate_best_score

        if search_info.quit:
            break

        # Only break out of iterative deepening if a winning mate is found.
        if best_score is not None and is_mate(best_score):
            break
        # print(best_move.to_text(), best_score, depth, time.time() - start_time)

        if max_depth is not None and depth == max_depth:
            break
        depth += 1
        if depth == 100: break

    return best_move



if __name__ == '__main__':
    # p = "0N2N0N0N0N1G1B3N0N1N1N1N0N1B2G2N1N0N0N0N0N0N0N0N0N0280"
    p = make_position(
        blocks=[
            0, 0, 0, 0, 0,
            0, 0, 0, 0, 0,
            0, 0, 1, 2, 0,
            0, 1, 0, 0, 0,
            0, 2, 2, 3, 0
        ],
        gray_workers=(7, 0),
        blue_workers=(16, 24),
        turn=1,  # Gray to move
        god_gray=God.ATLAS,
        god_blue=God.ATHENA,
        athena_up=False
    )
    board = Board(p)
    remaining_time_ms: int = 1000 * 60 * 10
    tt = TranspositionTable()
    bm = get_best_move(board, remaining_time_ms, tt, max_depth=3)
    print(bm.to_text())