from Board import Board
from search import get_best_move
from transposition_table import TranspositionTable
import cProfile

def main():
    p = "0N0N0N0N0B0N0N0N0G0N0N0G0N0N0N0N0N0N0N0N0N0B0N0N0N0040"
    board = Board(p)
    remaining_time_ms = 1000 * 60 * 10 * 50
    tt = TranspositionTable()
    cProfile.runctx('get_best_move(board, remaining_time_ms, tt, max_depth=4)', globals(), locals(), 'search.prof')

if __name__ == "__main__":
    main()
