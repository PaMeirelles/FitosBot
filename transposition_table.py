from typing import List, Optional

from Move import Move


class TTEntry:
    def __init__(self, hash_key: int, move: Move, depth: int, score: int, flag: str):
        self.hash_key = hash_key  # Unique hash for the board position
        self.move = move          # Best move from this position
        self.depth = depth        # Depth at which the score was computed
        self.score = score        # Evaluated score
        self.flag = flag          # 'A': upper bound, 'B': lower bound, 'E': exact


class TranspositionTable:
    def __init__(self, num_entries: int = (1 << 22)):
        """
        Initialize a fixed-size table.
        Default is 2^20 entries, but you can adjust this based on available memory.
        """
        self.num_entries: int = num_entries
        self.table: List[Optional[TTEntry]] = [None] * self.num_entries
        self.new_writes: int = 0
        self.overwrites: int = 0
        self.hits: int = 0
        self.cuts: int = 0

    def clear(self):
        self.table = [None] * self.num_entries
        self.new_writes = 0
        self.overwrites = 0
        self.hits = 0
        self.cuts = 0

    def store(self, board, move, score: int, depth: int, flag: str):
        """
        Store an entry in the transposition table using a fixed index.
        The flag is:
          - 'A' if the score is an upper bound (no improvement over alpha)
          - 'B' if the score is a lower bound (beta cutoff occurred)
          - 'E' if the score is exact (improved alpha)
        """
        key = hash(board)
        idx = key % self.num_entries
        if self.table[idx] is None:
            self.new_writes += 1
        else:
            self.overwrites += 1
        self.table[idx] = TTEntry(key, move, depth, score, flag)

    def probe(self, board, alpha: int, beta: int, depth: int):
        """
        Probe the table for an entry corresponding to the current board.
        Returns (move, score) if a stored entry exists that meets the depth requirement;
        otherwise returns (None, None).

        The logic is:
          - If flag == 'A' and stored score <= alpha, return alpha.
          - If flag == 'B' and stored score >= beta, return beta.
          - If flag == 'E', return the exact stored score.
        """
        key: int = hash(board)  # Use the built-in hash
        index = key % self.num_entries
        entry = self.table[index]
        if entry is not None and entry.hash_key == key and entry.depth >= depth:
            self.hits += 1
            if entry.flag == 'A' and entry.score <= alpha:
                return entry.move, alpha
            elif entry.flag == 'B' and entry.score >= beta:
                return entry.move, beta
            elif entry.flag == 'E':
                return entry.move, entry.score
        return None, None

    def probe_pv_move(self, board):
        """
        Retrieve the principal variation move (if any) for the given board.
        """
        key = hash(board)
        index = key % self.num_entries
        entry = self.table[index]
        if entry is not None and entry.hash_key == key:
            return entry.move, entry.score
        return None, None
