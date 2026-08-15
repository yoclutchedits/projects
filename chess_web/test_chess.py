from main import attempt_make_move, new_game_state

def test_basic_pawn_move():
    game_state = new_game_state()
    result = attempt_make_move(game_state, end = (4, 4), start = (6, 4), promote_to=None)
    assert result["success"] == True
    assert result["game_state"]["board"][6][4] is None 
    assert result["game_state"]["board"][4][4] == "wP" 
def test_illegal_move_rejected():
    game_state = new_game_state()
    # try moving a pawn 3 squares forward (illegal)
    result = attempt_make_move(game_state, end=(3, 4), start=(6, 4))
    assert result["success"] == False
    assert result["reason"] == "illegal_move" 


def test_wrong_turn_rejected():
    game_state = new_game_state()
    # Black tries to move first, but white always starts
    result = attempt_make_move(game_state, end=(3, 4), start=(1, 4))
    assert result["success"] == False
    assert result["reason"] == "wrong_turn"


def test_empty_square_rejected():
    game_state = new_game_state()
    # (3,3) is empty on a fresh board
    result = attempt_make_move(game_state, end=(2, 2), start=(3, 3))
    assert result["success"] == False
    assert result["reason"] == "illegal_move"


def test_en_passant_capture():
    game_state = new_game_state()

    attempt_make_move(game_state, end=(5, 0), start=(6, 0))  # white throwaway
    attempt_make_move(game_state, end=(3, 3), start=(1, 3))  # black double-step
    attempt_make_move(game_state, end=(5, 1), start=(6, 1))  # white throwaway
    attempt_make_move(game_state, end=(4, 3), start=(3, 3))  # black single-step
    attempt_make_move(game_state, end=(4, 4), start=(6, 4))  # white double-step

    result = attempt_make_move(game_state, end=(5, 4), start=(4, 3))  
    assert result["success"] == True
    assert result["game_state"]["board"][4][4] is None 
    assert result["game_state"]["board"][5][4] == "bP" 


def test_castling_kingside():
    game_state = new_game_state()

    attempt_make_move(game_state, end=(5, 6), start=(6, 6))  # white pawn opens diagonal
    attempt_make_move(game_state, end=(2, 0), start=(1, 0))  # black throwaway
    attempt_make_move(game_state, end=(6, 6), start=(7, 5))  # white bishop moves out
    attempt_make_move(game_state, end=(2, 1), start=(1, 1))  # black throwaway
    attempt_make_move(game_state, end=(5, 5), start=(7, 6))  # white knight moves out
    attempt_make_move(game_state, end=(2, 2), start=(1, 2))  # black throwaway

    result = attempt_make_move(game_state, end=(7, 6), start=(7, 4))  # white castles kingside

    assert result["success"] == True  # was the castle successful?
    assert result["game_state"]["board"][7][4] is None  # is (7,4) now empty? (king moved away)
    assert result["game_state"]["board"][7][6] == "wK"  # is (7,6) now occupied by the king?
    assert result["game_state"]["board"][7][5] == "wR" # is (7,5) now occupied by the rook? (rook should have moved too)
    assert result["game_state"]["board"][7][7] is None  # is (7,7) now empty? (rook moved away from there)

def test_castling_blocked_by_has_moved():
    game_state = new_game_state()

    attempt_make_move(game_state, end=(5, 6), start=(6, 6))
    attempt_make_move(game_state, end=(2, 0), start=(1, 0))
    attempt_make_move(game_state, end=(6, 6), start=(7, 5))
    attempt_make_move(game_state, end=(2, 1), start=(1, 1))
    attempt_make_move(game_state, end=(5, 5), start=(7, 6))
    attempt_make_move(game_state, end=(2, 2), start=(1, 2))
    attempt_make_move(game_state, end=(7, 5), start=(7, 4))   # king steps out
    attempt_make_move(game_state, end=(2, 3), start=(1, 3))
    attempt_make_move(game_state, end=(7, 4), start=(7, 5))   # king steps back
    attempt_make_move(game_state, end=(2, 4), start=(1, 4))

    result = attempt_make_move(game_state, end=(7, 6), start=(7, 4))  # attempt castle

    assert result["success"] == False # should this now fail?
    assert result["reason"] == "illegal_move" # what reason should it give?

def test_fools_mate_checkmate():
    game_state = new_game_state()

    attempt_make_move(game_state, end=(5, 5), start=(6, 5))
    attempt_make_move(game_state, end=(3, 4), start=(1, 4))
    attempt_make_move(game_state, end=(4, 6), start=(6, 6))

    result = attempt_make_move(game_state, end=(4, 7), start=(0, 3))  # checkmate move

    assert result["success"] == True # did the move succeed?
    assert result["game_state"]["game_over"] == True # is game_over now True?
    assert result["game_state"]["status_message"] == "Checkmate!"  # does status_message say "Checkmate!"?