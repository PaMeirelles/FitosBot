from Board import Board
from constants import God


def make_position(
    blocks,        # list of 25 integers in [0..4]
    gray_workers,  # tuple of 2 squares for Gray
    blue_workers,  # tuple of 2 squares for Blue
    turn,          # 1 => Gray to move, -1 => Blue to move
    god_gray,      # a Gods enum (e.g. Gods.APOLLO)
    god_blue,
    athena_up=False
) -> str:
    """
    Creates the canonical 54-char position string:
      - 25 pairs of (block height + worker code)
      - 1 char for turn
      - 1 char for god_gray (its numeric value)
      - 1 char for god_blue (its numeric value)
      - 1 char if athena went up last turn
    """
    if len(blocks) != 25:
        raise ValueError("blocks must have length 25")
    for b in blocks:
        if not (0 <= b <= 4):
            raise ValueError("Invalid block height, must be 0..4")
    position_chars = []
    for sq in range(25):
        h = blocks[sq]
        if sq in gray_workers:
            w = 'G'
        elif sq in blue_workers:
            w = 'B'
        else:
            w = 'N'
        position_chars.append(str(h))
        position_chars.append(w)
    turn_char = '0' if turn == 1 else '1'
    god_gray_char = str(god_gray.value)
    god_blue_char = str(god_blue.value)
    athena_char = '1' if athena_up else '0'
    return ''.join(position_chars) + turn_char + god_gray_char + god_blue_char + athena_char

def full_unmake_move_tests():
    """
    For each god in the Gods enum, create many test positions by varying:
      - The board block configuration,
      - Worker placements,
      - And active turn (Gray or Blue)
    For each board:
      1) Generate all moves.
      2) For every move, save the board state (using position_to_text),
         call make_move then unmake_move, and verify that the board state
         is exactly as before.
    """
    all_gods = list(God)
    test_positions = []

    # Define several block configurations:
    base_blocks1 = [0] * 25  # All zeros

    # A configuration with some non-zero blocks.
    base_blocks2 = [
        0, 1, 2, 0, 0,
        1, 2, 3, 0, 0,
        0, 0, 1, 1, 0,
        0, 2, 2, 1, 0,
        0, 0, 0, 1, 0
    ]
    base_blocks3 = [
        3, 2, 1, 0, 0,
        0, 1, 2, 3, 0,
        0, 0, 0, 0, 0,
        1, 2, 3, 4, 0,
        0, 0, 1, 2, 3
    ]
    block_configs = [base_blocks1, base_blocks2, base_blocks3]

    # Define several worker placements:
    workers_A = ((0, 1), (23, 24))        # Placement A
    workers_B = ((5, 7), (12, 14))         # Placement B
    workers_C = ((2, 10), (15, 24))        # Placement C
    workers_D = ((0, 12), (8, 20))         # Placement D
    worker_sets = [workers_A, workers_B, workers_C, workers_D]

    # For each god, create test positions for both turn values using all block configs and worker placements.
    for god in all_gods:
        for blocks in block_configs:
            for workers in worker_sets:
                gray_workers, blue_workers = workers
                # Test with Gray active: active god for Gray is 'god', Blue fixed (say, Apollo)
                pos_gray = make_position(
                    blocks=blocks,
                    gray_workers=gray_workers,
                    blue_workers=blue_workers,
                    turn=1,
                    god_gray=god,
                    god_blue=God.APOLLO,
                    athena_up=False
                )
                test_positions.append(pos_gray)
                # Test with Blue active: active god for Blue is 'god', Gray fixed (say, Apollo)
                pos_blue = make_position(
                    blocks=blocks,
                    gray_workers=gray_workers,
                    blue_workers=blue_workers,
                    turn=-1,
                    god_gray=God.APOLLO,
                    god_blue=god,
                    athena_up=False
                )
                test_positions.append(pos_blue)

    total_moves_tested = 0
    errors = 0

    for pos_str in test_positions:
        board = Board(pos_str)
        moves = board.generate_moves()
        if not moves:
            # Some positions might have no legal moves. Report and continue.
            print(f"No moves generated for position:\n{pos_str}\n--- skipping ---")
            continue

        for move in moves:
            before = board.position_to_text()
            board.make_move(move)
            board.unmake_move(move)
            after = board.position_to_text()
            total_moves_tested += 1
            if before != after:
                errors += 1
                print(f"ERROR: Board state mismatch after move {move}\nBefore: {before}\nAfter:  {after}\n")
        print(f"Test passed for position:\n{pos_str}\n  Moves tested: {len(moves)}\n")

    print(f"Total moves tested: {total_moves_tested}")
    if errors:
        print(f"Total errors found: {errors}")
    else:
        print("All unmake_move tests passed successfully.")

if __name__ == "__main__":
    full_unmake_move_tests()
