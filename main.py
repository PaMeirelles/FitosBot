from Board import Board, Gods
from Engine import SantoriniEngine
from Move import text_to_square


engine = SantoriniEngine()
engine.run()
# def make_position(
#     blocks,        # list of 25 integers in [0..4]
#     gray_workers,  # tuple of 2 squares for Gray
#     blue_workers,  # tuple of 2 squares for Blue
#     turn,          # 1 => Gray to move, -1 => Blue to move
#     god_gray,      # a Gods enum (e.g. Gods.APOLLO)
#     god_blue,
#     athena_up=False # a Gods enum (e.g. Gods.ARTEMIS)
# ) -> str:
#     """
#     Creates the canonical 54-char position string:
#       - 25 pairs of (block height + worker code)
#       - 1 char for turn
#       - 1 char for god_gray (its numeric value)
#       - 1 char for god_blue (its numeric value)
#       - 1 char if athena went up last turn
#     """
#     # Validate input quickly
#     if len(blocks) != 25:
#         raise ValueError("blocks must have length 25")
#     for b in blocks:
#         if not (0 <= b <= 4):
#             raise ValueError("Invalid block height, must be 0..4")
#     # Build the first 50 chars
#     position_chars = []
#     for sq in range(25):
#         # block height
#         h = blocks[sq]
#         # worker code
#         if sq == gray_workers[0] or sq == gray_workers[1]:
#             w = 'G'
#         elif sq == blue_workers[0] or sq == blue_workers[1]:
#             w = 'B'
#         else:
#             w = 'N'
#         position_chars.append(str(h))
#         position_chars.append(w)
#
#     # Turn: '0' => Gray, '1' => Blue
#     turn_char = '0' if turn == 1 else '1'
#     # Convert gods
#     god_gray_char = str(god_gray.value)
#     god_blue_char = str(god_blue.value)
#
#     athena_up = '1' if athena_up else '0'
#
#     return ''.join(position_chars) + turn_char + god_gray_char + god_blue_char + athena_up
#
#
# # blocks = [1, 0, 0, 3, 0, 1, 1, 4, 0, 3, 0, 4, 2, 0, 1, 0, 2, 2, 0, 0, 0, 0, 3, 1, 0]
# # board = Board(make_position(blocks, (13, 12), (18, 23), 1, Gods.APOLLO, Gods.ATHENA))
# board = Board("0N4N2N3N0B3N4N2G1N2N4N2N3N4N2N4N2B4N4N3N1N4N4N1G1N1090")
# moves = board.generate_moves()
# print(moves)
# for m in moves:
#     print(m.to_text())