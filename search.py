import time

from evaluate import score_position

###############################################################################
# Constants mirroring the C++ code
###############################################################################
MATE = 10000
CHECK_EVERY = 4096  # how often we check for time in the search
WIN = 9999          # sentinel for "this move is an instant win" (adjust if needed)

# The same "double-neighbor" bonus array as in your C++ code:
numDoubleNeighbors = [
    9,  12, 15, 12,  9,
    12, 16, 20, 16, 12,
    15, 20, 25, 20, 15,
    12, 16, 20, 16, 12,
    9,  12, 15, 12,  9
]

def get_time(remaining_time_ms: int) -> int:
    """
    Equivalent to your C++ timeManagement.cpp:
      int getTime(const int remainingTime) {
          return remainingTime / 10;
      }
    So if you have 5000 ms left, you'll think for ~500 ms.
    """
    return remaining_time_ms // 10

###############################################################################
# A small container to hold info for the search (mirrors your C++ SearchInfo).
###############################################################################
class SearchInfo:
    def __init__(self, board, depth, end_time):
        self.board = board            # Board reference
        self.depth = depth            # Current search depth
        self.nodes = 0                # Node counter
        self.quit = False             # Set to True if time runs out
        self.end_time = end_time      # Time (as float seconds) when we must stop
        self.bestMove = None          # Will store the best move found at this depth


###############################################################################
# Evaluate the position
###############################################################################
def evaluate(board) -> int:
    """
    Mirroring your C++ 'eval(b) * b->turn' logic:
      - board.score_position() is your static eval from Gray's perspective
      - Multiply by board.turn so the side to move tries to maximize
    """
    return score_position(board) * board.turn


###############################################################################
# Move Ordering
###############################################################################
def score_moves(moves, board):
    """
    Equivalent to your C++ 'score_moves(...)':
      moveOrderingScore = (move.toHeight - move.fromHeight)*10
                          + (numDoubleNeighbors[move.to] - numDoubleNeighbors[move.from])
    If you have a special "pvMove" logic in C++, skip it here since we’re not using a TT.
    """
    for mv in moves:
        # In your Board logic, 'mv.from_sq' is the worker's start, 'mv.final_sq' is the final,
        # and we can read heights from board.blocks.
        from_h = board.blocks[mv.from_sq]
        to_h   = board.blocks[mv.final_sq]
        # Score as in the C++ snippet:
        mv.moveOrderingScore = (to_h - from_h) * 10 \
                               + (numDoubleNeighbors[mv.final_sq] - numDoubleNeighbors[mv.from_sq])


def pick_move(moves, start_index: int):
    """
    Equivalent to C++ 'pickMove':
      - Among moves[start_index..end], find the one with the highest 'moveOrderingScore'
      - swap() it with moves[start_index].
    """
    best_idx = start_index
    best_score = moves[best_idx].moveOrderingScore
    for i in range(start_index + 1, len(moves)):
        if moves[i].moveOrderingScore > best_score:
            best_idx = i
            best_score = moves[i].moveOrderingScore
    if best_idx != start_index:
        moves[start_index], moves[best_idx] = moves[best_idx], moves[start_index]


###############################################################################
# The alpha-beta search function (mirroring your C++ 'search')
###############################################################################
def search(search_info: SearchInfo, depth: int, alpha: int, beta: int) -> int:
    # Increase the node count
    search_info.nodes += 1

    # Time check every CHECK_EVERY nodes
    if (search_info.nodes % CHECK_EVERY) == 0:
        if time.time() > search_info.end_time:
            # Time is up => signal quit, return 0
            search_info.quit = True
            search_info.bestMove = None
            return 0

    state = search_info.board.check_state()

    # If we are at leaf depth => return the evaluation
    if depth == 0 or state != 0:
        return evaluate(search_info.board)

    # Generate moves
    moves = search_info.board.generate_moves()
    if not moves:
        # No moves => losing position => return -MATE - depth
        return -MATE - depth

    # Track best move/score so we can store them in search_info
    max_score = -MATE * 100
    best_move = None

    # Move ordering
    score_moves(moves, search_info.board)

    for i in range(len(moves)):
        pick_move(moves, i)  # pick the best from moves[i..end] and swap into i
        move = moves[i]

        # Make the move
        search_info.board.make_move(move)
        # Recurse with "negated" window
        curr_score = -search(search_info, depth - 1, -beta, -alpha)
        # Unmake
        search_info.board.unmake_move(move)

        # Update best score
        if curr_score > max_score:
            max_score = curr_score
            best_move = move
            if max_score > alpha:
                # Raise alpha
                if max_score >= beta:
                    # Beta cutoff
                    search_info.bestMove = best_move
                    return beta
                alpha = max_score

        # If time is up (search_info.quit), bail out
        if search_info.quit:
            search_info.bestMove = None
            return 0

    # Store the best move in the SearchInfo so the caller can retrieve it
    search_info.bestMove = best_move
    # Return alpha (as in your C++ code's final 'return alpha;')
    return alpha


###############################################################################
# Iterative deepening driver (mirroring your C++ 'getBestMove')
###############################################################################
def get_best_move(board, remaining_time_ms: int):
    """
    1) Convert the remaining_time_ms to a 'thinkingTime'
    2) Start depth=1, do search => depth=2 => ...
    3) Stop if time is up or we found a forced mate
    4) Return the bestMove found at the last completed depth
    """
    thinking_time = get_time(remaining_time_ms)  # e.g. 1/10th of total
    start_time = time.time()
    end_time = start_time + (thinking_time / 1000.0)

    depth = 1
    best_move = None
    best_score = None

    while True:
        search_info = SearchInfo(board, depth, end_time)
        # Call alpha-beta
        result = search(search_info, depth, -MATE, MATE)
        # print(search_info.bestMove, result, depth, search_info.quit)
        if search_info.bestMove is not None:
            best_move = search_info.bestMove
            best_score = result

        # If we ran out of time, stop
        if search_info.quit:
            break

        # If the best move is effectively a mate (or leads to mate) => stop
        if best_move and (
            getattr(best_move, "build", None) == WIN
            or best_score > 9000
            or best_score < -9000
        ):
            break

        depth += 1
        # Also check the clock at the end of each iteration
        if time.time() > end_time:
            break

    return best_move
