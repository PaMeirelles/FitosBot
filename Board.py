from typing import List, Optional
from enum import Enum

from constants import NEIGHBOURS
from Move import Move, ApolloMove, ArtemisMove, AthenaMove, AtlasMove, DemeterMove, HephaestusMove, HermesMove, MinotaurMove, PanMove, \
    PrometheusMove


###############################################################################
# Enums, Constants, and Utility
###############################################################################

class Gods(Enum):
    APOLLO = 0
    ARTEMIS = 1
    ATHENA = 2
    ATLAS = 3
    DEMETER = 4
    HEPHAESTUS = 5
    HERMES = 6
    MINOTAUR = 7
    PAN = 8
    PROMETHEUS = 9

###############################################################################
# Board Class with Full God Logic
###############################################################################

def _god_move_match(god: Gods, move: Move) -> bool:
    """Quick check that (God -> Move type) pairing is correct at a class level."""
    god_to_move_type = {
        Gods.APOLLO: ApolloMove,
        Gods.ARTEMIS: ArtemisMove,
        Gods.ATHENA: AthenaMove,
        Gods.ATLAS: AtlasMove,
        Gods.DEMETER: DemeterMove,
        Gods.HEPHAESTUS: HephaestusMove,
        Gods.HERMES: HermesMove,
        Gods.MINOTAUR: MinotaurMove,
        Gods.PAN: PanMove,
        Gods.PROMETHEUS: PrometheusMove,
    }
    return isinstance(move, god_to_move_type.get(god, type(None)))


def _calculate_push_square(from_sq: int, to_sq: int) -> int:
    """
    Minotaur push: find the square in a straight line beyond 'to_sq' from 'from_sq'.
    E.g. if from_sq=12, to_sq=17 => the push goes 17->22 (just an example).
    We assume it's a valid push direction (i.e. same dx, same dy).
    """
    dx = (to_sq % 5) - (from_sq % 5)
    dy = (to_sq // 5) - (from_sq // 5)
    push_row = (to_sq // 5) + dy
    push_col = (to_sq % 5) + dx
    push_sq = push_row * 5 + push_col
    return push_sq


def _adj_ok(from_sq: int, to_sq: int) -> bool:
    return to_sq in NEIGHBOURS[from_sq]


class Board:
    def __init__(self, position: str):
        """
        position: 53-char string from the original code snippet, e.g.:
          block0 worker0 block1 worker1 ... block24 worker24 turn gods0 gods1
        """
        self.blocks = [0] * 25
        self.workers = [0] * 4
        self.turn = 1
        self.gods: List[Optional[Gods]] = [None, None]

        # Additional fields for god effects:
        self.prevent_up_next_turn = False        # Athena's effect
        self.last_move_height_diff = 0           # For Pan's special drop-win

        self.parse_position(position)

    def parse_position(self, position: str):
        if len(position) != 53:
            raise ValueError(f"Invalid position: Expected length 53, got {len(position)}")

        num_gray_workers = 0
        num_blue_workers = 0

        for i in range(25):
            height = int(position[2 * i])
            if height < 0 or height > 4:
                raise ValueError(f"Invalid block height at index {i}: {height}")
            self.blocks[i] = height

            worker_code = position[2 * i + 1]
            if worker_code == 'G':
                if num_gray_workers >= 2:
                    raise ValueError("Invalid position: More than 2 gray workers found")
                self.workers[num_gray_workers] = i
                num_gray_workers += 1
            elif worker_code == 'B':
                if num_blue_workers >= 2:
                    raise ValueError("Invalid position: More than 2 blue workers found")
                self.workers[2 + num_blue_workers] = i
                num_blue_workers += 1
            elif worker_code != 'N':
                raise ValueError(f"Invalid worker code '{worker_code}' at index {2 * i + 1}")

        if num_gray_workers != 2 or num_blue_workers != 2:
            raise ValueError(f"Invalid worker count: Found {num_gray_workers} gray workers and {num_blue_workers} blue workers")

        if position[50] == '0':
            self.turn = 1
        elif position[50] == '1':
            self.turn = -1
        else:
            raise ValueError(f"Invalid turn: Expected '0' or '1', got '{position[50]}'")

        try:
            self.gods[0] = Gods(int(position[51]))
            self.gods[1] = Gods(int(position[52]))
        except ValueError as e:
            raise ValueError(f"Invalid god indices at positions 51–52: {position[51:53]}") from e

    def position_to_text(self) -> str:
        position = []
        for i in range(25):
            block_height = str(self.blocks[i])
            if i in self.workers[:2]:
                worker_code = 'G'
            elif i in self.workers[2:]:
                worker_code = 'B'
            else:
                worker_code = 'N'
            position.append(block_height + worker_code)
        turn_char = '0' if self.turn == 1 else '1'
        god1 = str(self.gods[0].value)
        god2 = str(self.gods[1].value)
        return ''.join(position) + turn_char + god1 + god2

    def is_free(self, square: int) -> bool:
        """Check if 'square' is not occupied by a worker and is < 4 blocks tall."""
        return (square not in self.workers) and (self.blocks[square] < 4)

    def check_state(self) -> Optional[int]:
        """
        Returns:
          1  => Gray wins
         -1  => Blue wins
          0  => No terminal condition
        """
        # 1) Standard check: if any worker stands on height 3 => that player's color wins
        for i, worker_pos in enumerate(self.workers):
            if self.blocks[worker_pos] == 3:
                return 1 if i < 2 else -1

        # 2) Check if the current player just moved DOWN 2+ levels and is Pan => immediate win
        #    But be mindful which side actually moved. If "turn" was just flipped after make_move,
        #    the player who moved is the *opposite* of self.turn. So let's see who actually did it:
        last_player = -self.turn  # the side that made the last move
        if self.last_move_height_diff <= -2:
            # check if last_player is Pan
            idx = 0 if last_player == 1 else 1
            if self.gods[idx] == Gods.PAN:
                # Pan triggered a special drop-win
                return 1 if last_player == 1 else 0

        # 3) Check if the current player (self.turn) can move at all.
        #    If not, that player loses, the other wins.
        if not self._player_has_any_valid_move(self.turn):
            # current player cannot move => they lose
            return -self.turn

        return 0  # no terminal condition

    def move_is_valid(self, move: Move) -> bool:
        """Dispatch validation to the correct god logic (and do basic checks)."""
        current_player = 0 if self.turn == 1 else 1
        current_god = self.gods[current_player]

        # If the Move object doesn't correspond to this player's god, fail immediately:
        if not _god_move_match(current_god, move):
            return False

        # Before special checks, ensure the chosen worker is indeed theirs:
        if not self._worker_belongs_to_current_player(move):
            return False

        # If Athena effect is active, the *current* player is not allowed to move up
        # if self.prevent_up_next_turn is True.
        # (The official rule: "If Athena moved up last turn, the opponent CANNOT move up this turn.")
        # So if self.turn is the side that's *affected*, we forbid going up.
        if self.prevent_up_next_turn:
            if self._attempts_to_move_up(move):
                return False

        # Now do god-specific checks:
        if isinstance(move, ApolloMove) and current_god == Gods.APOLLO:
            return self._apollo_move_is_valid(move)
        elif isinstance(move, ArtemisMove) and current_god == Gods.ARTEMIS:
            return self._artemis_move_is_valid(move)
        elif isinstance(move, AthenaMove) and current_god == Gods.ATHENA:
            return self._athena_move_is_valid(move)
        elif isinstance(move, AtlasMove) and current_god == Gods.ATLAS:
            return self._atlas_move_is_valid(move)
        elif isinstance(move, DemeterMove) and current_god == Gods.DEMETER:
            return self._demeter_move_is_valid(move)
        elif isinstance(move, HephaestusMove) and current_god == Gods.HEPHAESTUS:
            return self._hephaestus_move_is_valid(move)
        elif isinstance(move, HermesMove) and current_god == Gods.HERMES:
            return self._hermes_move_is_valid(move)
        elif isinstance(move, MinotaurMove) and current_god == Gods.MINOTAUR:
            return self._minotaur_move_is_valid(move)
        elif isinstance(move, PanMove) and current_god == Gods.PAN:
            return self._pan_move_is_valid(move)
        elif isinstance(move, PrometheusMove) and current_god == Gods.PROMETHEUS:
            return self._prometheus_move_is_valid(move)

        # If none matched, it's invalid
        return False

    def _make_move_for_god(self, current_god: Gods, move: Move):
        god_move_handlers = {
            Gods.APOLLO: (ApolloMove, self._apollo_make_move),
            Gods.ARTEMIS: (ArtemisMove, self._artemis_make_move),
            Gods.ATHENA: (AthenaMove, self._athena_make_move),
            Gods.ATLAS: (AtlasMove, self._atlas_make_move),
            Gods.DEMETER: (DemeterMove, self._demeter_make_move),
            Gods.HEPHAESTUS: (HephaestusMove, self._hephaestus_make_move),
            Gods.HERMES: (HermesMove, self._hermes_make_move),
            Gods.MINOTAUR: (MinotaurMove, self._minotaur_make_move),
            Gods.PAN: (PanMove, self._pan_make_move),
            Gods.PROMETHEUS: (PrometheusMove, self._prometheus_make_move),
        }

        move_class, handler = god_move_handlers.get(current_god, (None, None))
        if move_class and isinstance(move, move_class):
            handler(move)
        else:
            raise Exception("Unrecognized god/move combination in make_move")

    def make_move(self, move: Move) -> None:
        """Perform the actual move, applying the correct god's special logic."""
        if not self.move_is_valid(move):
            raise Exception("Invalid move")

        current_player = 0 if self.turn == 1 else 1
        current_god = self.gods[current_player]

        # We'll reset last_move_height_diff each time we do a move.
        self.last_move_height_diff = 0

        self._make_move_for_god(current_god, move)

        # After the move is applied, check if the current god is Athena and if they moved up.
        # If so, set the flag to prevent the next player from moving up:
        if current_god == Gods.ATHENA and self.last_move_height_diff > 0:
            self.prevent_up_next_turn = True
        else:
            # Otherwise, if the player wasn't Athena (or didn't move up),
            # we clear the effect (the next player is free to move up).
            self.prevent_up_next_turn = False

        # Switch turn to the other side
        self.turn *= -1

    ############################################################################
    #                           GOD-SPECIFIC CHECKS
    ############################################################################

    def _worker_belongs_to_current_player(self, move: Move) -> bool:
        """
        Check if move.from_sq is indeed owned by the current player.
         - If self.turn == 1 => workers[0..1]
         - If self.turn == -1 => workers[2..3]
        """
        from_sq = move.from_sq
        if self.turn == 1:
            return from_sq in (self.workers[0], self.workers[1])
        else:
            return from_sq in (self.workers[2], self.workers[3])

    def _attempts_to_move_up(self, move: Move) -> bool:
        """Check if from->to is an upward movement of at least +1 block."""
        from_height = self.blocks[move.from_sq]
        to_height = self.blocks[move.final_sq]
        return to_height > from_height

    def _player_has_any_valid_move(self, side: int) -> bool:
        current_player = 0 if side == 1 else 1
        god = self.gods[current_player]
        worker_indices = [0, 1] if side == 1 else [2, 3]

        for wi in worker_indices:
            wpos = self.workers[wi]
            for to_sq in NEIGHBOURS[wpos]:
                if self.blocks[to_sq] == 4:
                    continue  # cannot move to dome


                from_h = self.blocks[wpos]
                to_h = self.blocks[to_sq]

                if god == Gods.HERMES:
                    if from_h == 0 and self.is_free(to_sq):
                        return True

                if to_h - from_h > 1:
                    continue  # too high to climb

                if to_h - from_h == 1 and self.prevent_up_next_turn:
                    continue

                occupant = self._which_worker_is_here(to_sq)
                if occupant is None:
                    return True

                # Special movement cases:
                if god == Gods.APOLLO:
                    if self._is_opponent_worker(occupant):
                        return True

                elif god == Gods.MINOTAUR:
                    if self._is_opponent_worker(occupant):
                        push_sq = _calculate_push_square(wpos, to_sq)
                        if 0 <= push_sq < 25 and self.is_free(push_sq):
                            return True


        return False

    def _which_worker_is_here(self, sq: int) -> Optional[int]:
        """Return the index of self.workers if any worker stands on 'sq', else None."""
        for i, wpos in enumerate(self.workers):
            if wpos == sq:
                return i
        return None

    def _is_opponent_worker(self, worker_index: int) -> bool:
        """True if worker_index belongs to the opposite color from self.turn."""
        if self.turn == 1:
            # We are gray => opponent is indexes [2,3]
            return worker_index in (2, 3)
        else:
            # We are blue => opponent is indexes [0,1]
            return worker_index in (0, 1)

    def _move_worker(self, move: Move) -> None:
        for i, wpos in enumerate(self.workers):
            if wpos == move.from_sq:
                self.workers[i] = move.final_sq
                break

    def _height_ok(self, from_sq: int, to_sq: int) -> bool:
        from_h = self.blocks[from_sq]
        to_h = self.blocks[to_sq]
        return to_h - from_h <= 1

    def _height_and_adj_ok(self, move: Move):
        return self._height_ok(move.from_sq, move.final_sq) and _adj_ok(move.from_sq, move.final_sq)

    def _build_ok_sq(self, from_sq: int, to_sq:int, build_sq: int) -> bool:
        return build_sq in NEIGHBOURS[to_sq] and to_sq != build_sq and (from_sq == build_sq or self.is_free(build_sq))

    def _move_checks(self, move: Move) -> bool:
        return self._height_and_adj_ok(move) and self.is_free(move.final_sq)

    def _move_checks_sq(self, from_sq: int, final_sq: int) -> bool:
        return self._height_ok(from_sq, final_sq) and _adj_ok(from_sq, final_sq) and self.is_free(final_sq)

    def _complete_checks_sq(self, from_sq: int, to_sq:int, build_sq: int) -> bool:
        return self._move_checks_sq(from_sq, to_sq) and self._build_ok_sq(from_sq, to_sq, build_sq)
    ############################################################################
    #               GOD-SPECIFIC VALIDATION & EXECUTION
    ############################################################################

    # --------------------------
    # APOLLO
    # --------------------------
    def _apollo_move_is_valid(self, move: ApolloMove) -> bool:
        if not self._height_and_adj_ok(move):
            return False

        # With Apollo, you can swap if occupant is an opponent.
        # If occupant is your own worker, or a tower (4 blocks), it's invalid.
        occupant = self._which_worker_is_here(move.to_sq)
        if occupant is not None:
            # must be opponent's worker for a valid Apollo swap
            if not self._is_opponent_worker(occupant):
                return False
        else:
            # If it's empty, we also must ensure it's not a dome
            if self.blocks[move.to_sq] == 4:
                return False

        if not self._build_ok_sq(move.from_sq, move.to_sq, move.build_sq):
            return False
        elif self._is_opponent_worker(occupant) and move.from_sq == move.build_sq:
            return False
        return True

    def _apollo_make_move(self, move: ApolloMove):
        occupant_index = self._which_worker_is_here(move.to_sq)
        if occupant_index is not None:
            if not self._is_opponent_worker(occupant_index):
                raise Exception("Apollo cannot swap with allied worker")
            self.workers[occupant_index] = move.from_sq

        # Move active worker
        self._move_worker(move)

        # Build
        self.blocks[move.build_sq] += 1

    # --------------------------
    # ARTEMIS
    # --------------------------
    def _artemis_move_is_valid(self, move: ArtemisMove) -> bool:
        """
        Artemis can move twice, but cannot return to the original square.
        - If mid_sq is not None, it indicates a two-step movement:
          from_sq -> mid_sq -> to_sq, each step must be valid adjacency
          and cannot climb more than 1 level, nor step onto a dome.
          Also 'to_sq' must not be the same as 'from_sq'.
        - Then build_sq must be adjacent to 'to_sq' and not a dome.
        """
        # Always check the first step (from->mid or from->to)
        if move.mid_sq is None:
            if not self._move_checks(move):
                return False
        else:
            # Two-step
            # step1: from_sq -> mid_sq
            if not self._move_checks_sq(move.from_sq, move.mid_sq):
                return False

            # step2: mid_sq -> to_sq
            if not self._move_checks_sq(move.mid_sq, move.to_sq):
                return False

            if move.to_sq == move.from_sq:
                return False

        if not self._build_ok_sq(move.from_sq, move.final_sq, move.build_sq):
            return False

        return True

    def _artemis_make_move(self, move: ArtemisMove):
        path = [move.from_sq]
        if move.mid_sq is not None:
            path.append(move.mid_sq)
        path.append(move.to_sq)

        # Move step by step
        for i, wpos in enumerate(self.workers):
            if wpos == move.from_sq:
                for sq in path[1:]:
                    if self._which_worker_is_here(sq) is not None:
                        raise Exception("Artemis invalid: move path occupied!")
                    self.workers[i] = sq
                break

        # Build
        self.blocks[move.build_sq] += 1


    # --------------------------
    # ATHENA
    # --------------------------
    def _athena_move_is_valid(self, move: AthenaMove) -> bool:
        """Basically the same as a standard single-step move (like Apollo) but no swap."""
        return self._complete_checks_sq(move.from_sq, move.to_sq, move.build_sq)

    def _athena_make_move(self, move: AthenaMove):
        self._move_worker(move)
        self.blocks[move.build_sq] += 1
        from_h = self.blocks[move.from_sq]
        to_h = self.blocks[move.to_sq]
        self.last_move_height_diff = to_h - from_h

    # --------------------------
    # ATLAS
    # --------------------------
    def _atlas_move_is_valid(self, move: AtlasMove) -> bool:
        return self._complete_checks_sq(move.from_sq, move.to_sq, move.build_sq)

    def _atlas_make_move(self, move: AtlasMove):
        self._move_worker(move)

        # Build (dome if move.dome==True, otherwise +1)
        if move.dome:
            self.blocks[move.build_sq] = 4
        else:
            self.blocks[move.build_sq] += 1


    # --------------------------
    # DEMETER
    # --------------------------
    def _demeter_move_is_valid(self, move: DemeterMove) -> bool:
        if not self._complete_checks_sq(move.from_sq, move.to_sq, move.build_sq_1):
            return False

        if move.build_sq_2 is not None:
            # must be different from build_sq_1
            if move.build_sq_2 == move.build_sq_1:
                return False
            if not self._build_ok_sq(move.from_sq, move.to_sq, move.build_sq_2):
                return False

        return True

    def _demeter_make_move(self, move: DemeterMove):
        self._move_worker(move)

        # Build first
        self.blocks[move.build_sq_1] += 1
        # Build second if provided
        if move.build_sq_2 is not None:
            self.blocks[move.build_sq_2] += 1


    # --------------------------
    # HEPHAESTUS
    # --------------------------
    def _hephaestus_move_is_valid(self, move: HephaestusMove) -> bool:
        """
        Similar to Demeter but the second build, if used, must be on the same square,
        and we cannot build a dome this way (so the second block cannot raise to 4).
        """
        if not self._complete_checks_sq(move.from_sq, move.to_sq, move.build_sq_1):
            return False

        if move.build_sq_2 is not None:
            # must be different from build_sq_1
            if move.build_sq_2 != move.build_sq_1 or self.blocks[move.build_sq_2] >= 2:
                return False
            if not self._build_ok_sq(move.from_sq, move.to_sq, move.build_sq_2):
                return False

        return True

    def _hephaestus_make_move(self, move: HephaestusMove):
        self._move_worker(move)

        # Build first block
        self.blocks[move.build_sq_1] += 1
        # If there's a second build on same square, do it but do not create a dome
        if move.build_sq_2 is not None:
            self.blocks[move.build_sq_2] += 1

    # --------------------------
    # HERMES
    # --------------------------
    def _hermes_move_is_valid(self, move: HermesMove) -> bool:
        """
        Hermes can move multiple times, but only on level 0 if continuing to move.
        Officially: if you start on level 0, you may keep walking on 0's.
        The big rule: "You may move your Worker any number of times, but each move must be on ground level (0) only
        or you can just do a normal single-step if you like. After moving, build once normally."
        """
        if len(move.squares) == 1:
            return self._complete_checks_sq(move.from_sq, move.final_sq, move.build_sq)


        current_pos = move.from_sq
        staring_height = self.blocks[move.from_sq]

        for idx, nxt in enumerate(move.squares):
            if self.blocks[nxt] != staring_height:
                return False

            if not self._move_checks_sq(current_pos, nxt):
                return False

            current_pos = nxt

        if not self._build_ok_sq(move.from_sq, move.final_sq, move.build_sq):
            return False
        return True

    def _hermes_make_move(self, move: HermesMove):
        self._move_worker(move)
        self.blocks[move.build_sq] += 1

    # --------------------------
    # MINOTAUR
    # --------------------------
    def _minotaur_move_is_valid(self, move: MinotaurMove) -> bool:
        if not self._height_and_adj_ok(move):
            return False

        occupant = self._which_worker_is_here(move.to_sq)
        if occupant is not None:
            if not self._is_opponent_worker(occupant):
                return False
            push_sq = _calculate_push_square(move.from_sq, move.to_sq)
            if not (0 <= push_sq < 25) or not self.is_free(push_sq):
                return False
        else:
            if self.blocks[move.to_sq] == 4:
                return False

        if not self._build_ok_sq(move.from_sq, move.to_sq, move.build_sq):
            return False

        return True

    def _minotaur_make_move(self, move: MinotaurMove):
        occupant_index = self._which_worker_is_here(move.to_sq)
        if occupant_index is not None:
            if not self._is_opponent_worker(occupant_index):
                raise Exception("Minotaur cannot push allied worker")
            push_sq = _calculate_push_square(move.from_sq, move.to_sq)
            if not (0 <= push_sq < 25) or not self.is_free(push_sq):
                raise Exception("Invalid Minotaur push destination")
            self.workers[occupant_index] = push_sq

        # Move active worker
        self._move_worker(move)

        # Build
        self.blocks[move.build_sq] += 1


    # --------------------------
    # PAN
    # --------------------------
    def _pan_move_is_valid(self, move: PanMove) -> bool:
        return self._complete_checks_sq(move.from_sq, move.final_sq, move.build_sq)

    def _pan_make_move(self, move: PanMove):
        from_height = self.blocks[move.from_sq]

        self._move_worker(move)

        # Build
        self.blocks[move.build_sq] += 1

        to_height = self.blocks[move.to_sq]
        self.last_move_height_diff = to_height - from_height

    # --------------------------
    # PROMETHEUS
    # --------------------------
    def _prometheus_move_is_valid(self, move: PrometheusMove) -> bool:
        if move.optional_build is None:
            return self._complete_checks_sq(move.from_sq, move.to_sq, move.build_sq)

        if not self._build_ok_sq(move.from_sq, move.from_sq, move.optional_build):
            return False
        if self.blocks[move.to_sq] > self.blocks[move.from_sq]:
            return False  # cannot move up after building
        if not self._complete_checks_sq(move.from_sq, move.to_sq, move.build_sq):
            return False

        return True

    def _prometheus_make_move(self, move: PrometheusMove):
        if move.optional_build is not None:
            self.blocks[move.optional_build] += 1

        self._move_worker(move)
        self.blocks[move.build_sq] += 1

    def _get_worker_index(self):
        if self.turn == 1:
            return self.workers[:2]
        else:
            return self.workers[2:]

    def _get_build_sq(self, from_sq: int, to_sq: int) -> List[int]:
        sq = []
        for build_sq in NEIGHBOURS[to_sq]:
            if not self.is_free(build_sq) and build_sq != from_sq:
                continue
            if build_sq == to_sq:
                continue
            sq.append(build_sq)
        return sq

    def _generate_moves_athena(self):
        worker_index = self._get_worker_index()

        moves = []

        for wi in worker_index:
            from_sq = self.workers[wi]
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - self.blocks[from_sq] > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(AthenaMove(from_sq, to_sq, build_sq))
        return moves

    def _is_ally_worker(self, sq: int) -> bool:
        return not self._is_opponent_worker(sq)

    def _generate_moves_apollo(self):
        worker_index = self._get_worker_index()
        moves = []

        for wi in worker_index:
            from_sq = wi
            for to_sq in NEIGHBOURS[from_sq]:
                occupant = self._which_worker_is_here(to_sq)
                if (self.blocks[to_sq] == 4 or (occupant is not None and self._is_ally_worker(occupant)) or
                        self.blocks[to_sq] - self.blocks[from_sq] > 1):
                    continue
                for build_sq in NEIGHBOURS[to_sq]:
                    if not self.is_free(build_sq) and (build_sq != from_sq or (occupant is not None and self._is_ally_worker(occupant))):
                        continue
                    if build_sq == to_sq:
                        continue
                    moves.append(ApolloMove(from_sq, to_sq, build_sq))
        return moves

    def _generate_moves_artemis(self):
        worker_index = self._get_worker_index()

        moves = []

        for wi in worker_index:
            from_sq = wi
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - self.blocks[from_sq] > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(ArtemisMove(from_sq, to_sq, build_sq))
                for second_move_sq in NEIGHBOURS[to_sq]:
                    if (not self.is_free(second_move_sq) or self.blocks[second_move_sq] - self.blocks[to_sq] > 1 or
                            second_move_sq == from_sq):
                        continue
                    build_sqs = self._get_build_sq(from_sq, second_move_sq)
                    for build_sq in build_sqs:
                        moves.append(ArtemisMove(from_sq, second_move_sq, build_sq))
        return moves

    def _generate_moves_atlas(self):
        worker_index = self._get_worker_index()

        moves = []

        for wi in worker_index:
            from_sq = wi
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - self.blocks[from_sq] > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(AtlasMove(from_sq, to_sq, build_sq, False))
                    if self.blocks[build_sq] != 4:
                        moves.append(AtlasMove(from_sq, to_sq, build_sq, True))
        return moves

    def _generate_moves_demeter(self):
        worker_index = self._get_worker_index()

        moves = []

        for wi in worker_index:
            from_sq = wi
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - self.blocks[from_sq] > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq_1 in build_sqs:
                    for build_sq_2 in build_sqs:
                        if build_sq_1 == build_sq_2:
                            moves.append(DemeterMove(from_sq, to_sq, build_sq_1))
                        else:
                            moves.append(DemeterMove(from_sq, to_sq, build_sq_1, build_sq_2))
        return moves

    def _generate_moves_hephaestus(self):
        worker_index = self._get_worker_index()

        moves = []

        for wi in worker_index:
            from_sq = wi
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - self.blocks[from_sq] > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(DemeterMove(from_sq, to_sq, build_sq))
                    moves.append(DemeterMove(from_sq, to_sq, build_sq, build_sq))
        return moves

    def _generate_moves_pan(self):
        worker_index = self._get_worker_index()

        moves = []

        for wi in worker_index:
            from_sq = wi
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - self.blocks[from_sq] > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(PanMove(from_sq, to_sq, build_sq))
        return moves

    def _generate_moves_hermes(self):
        worker_index = self._get_worker_index()
        moves = []

        for wi in worker_index:
            from_sq = wi
            from_h = self.blocks[from_sq]

            # Single-step normal moves
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - from_h > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(HermesMove(from_sq, [to_sq], build_sq))

            visited = set()
            stack = [(from_sq, [from_sq])]
            while stack:
                current_sq, path = stack.pop()
                for nei in NEIGHBOURS[current_sq]:
                    if nei in visited:
                        continue
                    if nei in path or not self.is_free(nei):
                        continue
                    if self.blocks[nei] != from_h:
                        continue
                    new_path = path + [nei]
                    build_sqs = self._get_build_sq(from_sq, nei)
                    for build_sq in build_sqs:
                        moves.append(HermesMove(from_sq, new_path[1:], build_sq))  # exclude from_sq
                    stack.append((nei, new_path))
                    visited.add(nei)
        return moves

    def _generate_moves_minotaur(self):
        worker_index = self._get_worker_index()
        moves = []

        for wi in worker_index:
            from_sq = wi
            from_h = self.blocks[from_sq]

            for to_sq in NEIGHBOURS[from_sq]:
                occupant = self._which_worker_is_here(to_sq)
                if occupant is None or self._is_ally_worker(occupant):
                    continue
                if self.blocks[to_sq] == 4 or self.blocks[to_sq] - from_h > 1:
                    continue

                # compute push destination
                dx = to_sq % 5 - from_sq % 5
                dy = to_sq // 5 - from_sq // 5
                push_sq = to_sq + dx + dy * 4  # same as: to_sq + (to_sq - from_sq)

                if not (0 <= push_sq < 25):
                    continue
                if not self.is_free(push_sq):
                    continue
                if self.blocks[push_sq] == 4:
                    continue

                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(MinotaurMove(from_sq, to_sq, build_sq))

        return moves

    def _generate_moves_prometheus(self):
        worker_index = self._get_worker_index()
        moves = []

        for wi in worker_index:
            from_sq = wi
            from_h = self.blocks[from_sq]

            # Option 1: normal move without optional build
            for to_sq in NEIGHBOURS[from_sq]:
                if not self.is_free(to_sq) or self.blocks[to_sq] - from_h > 1:
                    continue
                build_sqs = self._get_build_sq(from_sq, to_sq)
                for build_sq in build_sqs:
                    moves.append(PrometheusMove(from_sq, to_sq, build_sq))

            # Option 2: build first, then move (but can't move up)
            prebuild_sqs = self._get_build_sq(from_sq, from_sq)
            for opt_build_sq in prebuild_sqs:
                if self.blocks[opt_build_sq] == 4:
                    continue
                for to_sq in NEIGHBOURS[from_sq]:
                    if not self.is_free(to_sq):
                        continue
                    if self.blocks[to_sq] > from_h:
                        continue  # can't move up after building first
                    build_sqs = self._get_build_sq(from_sq, to_sq)
                    for build_sq in build_sqs:
                        moves.append(PrometheusMove(from_sq, to_sq, build_sq, optional_build=opt_build_sq))
        return moves

    def generate_moves(self):
        god = self.gods[0] if self.turn == 1 else self.gods[1]

        dispatch = {
            Gods.APOLLO: self._generate_moves_apollo,
            Gods.ARTEMIS: self._generate_moves_artemis,
            Gods.ATHENA: self._generate_moves_athena,
            Gods.ATLAS: self._generate_moves_atlas,
            Gods.DEMETER: self._generate_moves_demeter,
            Gods.HEPHAESTUS: self._generate_moves_hephaestus,
            Gods.HERMES: self._generate_moves_hermes,
            Gods.MINOTAUR: self._generate_moves_minotaur,
            Gods.PAN: self._generate_moves_pan,
            Gods.PROMETHEUS: self._generate_moves_prometheus,
        }

        return dispatch.get(god)()





