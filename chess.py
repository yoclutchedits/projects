
def create_board():
    board = [[None for _ in range(8)] for _ in range(8)]
    return board

def print_board(board):
    for row in board:
        line = ""
        for cell in row:
            line += (cell if cell else "..") + " "
        print(line)

def place_piece(board, row, col, piece):
    board[row][col] = piece

def setup_pawns(board):
    for col in range(8):
        place_piece(board, 1, col, "bP")
        place_piece(board, 6, col, "wP")

def setup_back_rank(board):
    order = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    for col, piece_type in enumerate(order):
        place_piece(board, 0, col, "b" + piece_type)
        place_piece(board, 7, col, "w" + piece_type)

def is_valid_pawn_move(board, start, end):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    if piece is None or piece[1] != "P":
        return False  # not a pawn
    color = piece[0]  # "w" or "b"
    direction = -1 if color == "w" else 1
    target = board[er][ec]
    one_step = (er == sr + direction) and (ec == sc) and (target is None)
    starting_row = 6 if color == "w" else 1
    in_between = board[sr + direction][sc]
    two_step = (
    er == sr + 2*direction
    and ec == sc
    and target is None
    and in_between is None
    and sr == starting_row
)   
    capture = (
    er == sr + direction
    and abs(ec - sc) == 1
    and target is not None
    and target[0] != color
)
    return one_step or two_step or capture

def is_valid_king_move(board, start, end):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    if piece is None or piece[1] != "K":
        return False  # not a king
    color = piece[0]  # "w" or "b"
    target = board[er][ec]
    row_diff = abs(er - sr)
    col_diff = abs(ec - sc)
    if (row_diff <= 1 and col_diff <= 1) and (row_diff != 0 or col_diff != 0)  and (target is None or target[0] != color):
        return True
    return False

def is_valid_rook_move(board, start, end):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    same_row = (sr == er)
    same_col = (sc == ec)
    moves_straight = same_row != same_col
    if piece is None or piece[1] != "R":
        return False  # not a rook
    color = piece[0]  # "w" or "b"
    target = board[er][ec]
    if target is not None and target[0] == color:
        return False  # can't capture own piece
    if moves_straight:
        if same_row:
            step = 1 if ec > sc else -1
            for c in range(sc + step, ec, step):
                if board[sr][c] is not None:
                    return False  # path blocked
        else:  # same_col
            step = 1 if er > sr else -1
            for r in range(sr + step, er, step):
                if board[r][sc] is not None:
                    return False  # path blocked
        return True
    return False

def is_valid_bishop_move(board, start, end):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    row_diff = abs(er - sr)
    col_diff = abs(ec - sc)
    is_diagonal = row_diff == col_diff and row_diff != 0
    if piece is None or piece[1] != "B":
        return False  # not a bishop
    color = piece[0]  # "w" or "b"
    target = board[er][ec]
    if target is not None and target[0] == color:
        return False  # can't capture own piece
    if is_diagonal:
        step_row = 1 if er > sr else -1
        step_col = 1 if ec > sc else -1
        for r, c in zip(range(sr + step_row, er, step_row), range(sc + step_col, ec, step_col)):
            if board[r][c] is not None:
                return False  # path blocked
        return True
    return False

def is_valid_queen_move(board, start, end):
    sr, sc = start
    piece = board[sr][sc]
    if piece is None or piece[1] != "Q":
        return False  # not a queen
    color = piece[0]

    board[sr][sc] = color + "R"
    rook_style = is_valid_rook_move(board, start, end)
    board[sr][sc] = color + "B"
    bishop_style = is_valid_bishop_move(board, start, end)
    board[sr][sc] = piece  # restore the real queen

    return rook_style or bishop_style

def is_valid_knight_move(board, start, end):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    if piece is None or piece[1] != "N":
        return False

    color = piece[0]
    target = board[er][ec]
    row_diff = abs(er - sr)
    col_diff = abs(ec - sc)

    if (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2):
        if target is None or target[0] != color:
            return True
    return False

def is_valid_move(board, start, end):
    sr, sc = start
    piece = board[sr][sc]
    if piece is None:
        return False
    piece_type = piece[1]

    if piece_type == "P":
        return is_valid_pawn_move(board, start, end)
    elif piece_type == "K":
        return is_valid_king_move(board, start, end)
    elif piece_type == "R":
        return is_valid_rook_move(board, start, end)
    elif piece_type == "B":
        return is_valid_bishop_move(board, start, end)
    elif piece_type == "Q":
        return is_valid_queen_move(board, start, end)
    elif piece_type == "N":
        return is_valid_knight_move(board, start, end)
    return False

def make_move(board, start, end, promote_to=None):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    board[er][ec] = piece
    board[sr][sc] = None
    if piece[1] == "P" and (er == 0 or er == 7):
        if promote_to is None:
            while True:
                promotion = input("Promote pawn to (Q, R, B, N): ").upper()
                if promotion in ["Q", "R", "B", "N"]:
                    promote_to = promotion
                    break
                else:
                    print("Invalid promotion choice. Please choose Q, R, B, or N.")
        board[er][ec] = piece[0] + promote_to

def find_king(board, color):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece is not None and piece[1] == "K" and piece[0] == color:
                return (row, col)
    return None

def is_in_check(board, color):
    king_pos = find_king(board, color)
    enemy_color = "b" if color == "w" else "w"
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece is not None and piece[0] == enemy_color:
                is_valid = is_valid_move(board, (row, col), king_pos)
                if is_valid:
                    return True
    return False

def is_en_passant_safe(board, start, end, last_move, color):
    if not is_valid_en_passant(board, start, end, last_move):
        return False

    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    captured_pawn = board[sr][ec]

    # Temporarily simulate En Passant
    board[er][ec] = piece
    board[sr][sc] = None
    board[sr][ec] = None

    still_in_check = is_in_check(board, color)

    # Revert board
    board[sr][sc] = piece
    board[er][ec] = None
    board[sr][ec] = captured_pawn

    return not still_in_check

def has_any_legal_move(board, color, last_move=None):
    for sr in range(8):
        for sc in range(8):
            piece = board[sr][sc]
            if piece is None or piece[0] != color:
                continue
            for er in range(8):
                for ec in range(8):
                    start = (sr, sc)
                    end = (er, ec)
                    if is_move_safe(board, start, end, color):
                        return True
                    if piece[1] == "P" and is_en_passant_safe(board, start, end, last_move, color):
                        return True
    return False

def is_checkmate(board, color, last_move=None):
    return is_in_check(board, color) and not has_any_legal_move(board, color, last_move)

def is_stalemate(board, color, last_move=None):
    return not is_in_check(board, color) and not has_any_legal_move(board, color, last_move)

def is_move_safe(board, start, end, color):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]
    if not is_valid_move(board, start, end):
        return False

    original_piece = board[er][ec]
    make_move(board, start, end, promote_to="Q")
    still_in_check = is_in_check(board, color)
    board[sr][sc] = piece
    board[er][ec] = original_piece

    return not still_in_check

def is_insufficient_material(board):
    pieces = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece is not None:
                pieces.append(piece)
    non_kings = [p for p in pieces if p[1] != "K"]
    if len(non_kings) == 0:
        return True  # just the two kings
    if len(non_kings) == 1 and non_kings[0][1] in ("B", "N"):
        return True  # king + bishop/knight vs king
    if len(non_kings) == 2:
        p1, p2 = non_kings
        if p1[1] == "B" and p2[1] == "B" and p1[0] != p2[0]:
            return True  # king+bishop vs king+bishop, opposite sides
    return False

def is_valid_en_passant(board, start, end, last_move):

    if not last_move:
        return False

    sr, sc = start
    er, ec = end
    piece = board[sr][sc]

    if piece is None or piece[1] != "P":
        return False

    color = piece[0]
    direction = -1 if color == "w" else 1

    # Must move one step diagonally into an empty destination
    if er != sr + direction or abs(ec - sc) != 1 or board[er][ec] is not None:
        return False

    # Check last move: enemy pawn moved 2 ranks to land directly next to our pawn
    (last_sr, last_sc), (last_er, last_ec), last_piece = last_move
    enemy_color = "b" if color == "w" else "w"

    if last_piece == enemy_color + "P":
        if abs(last_er - last_sr) == 2 and last_er == sr and last_ec == ec:
            return True

    return False

def make_en_passant(board, start, end):
    sr, sc = start
    er, ec = end
    piece = board[sr][sc]

    # Move current pawn
    board[er][ec] = piece
    board[sr][sc] = None

    # Remove captured pawn (located on starting row, target column)
    board[sr][ec] = None

def is_square_attacked(board, square, by_color):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece is not None and piece[0] == by_color:
                if is_valid_move(board, (row, col), square):
                    return True
    return False

def is_castling_legal(board, color, side, has_moved):
    """
    side: "kingside" or "queenside"
    """
    king_row = 7 if color == "w" else 0
    if side == "kingside":
        if has_moved.get((color, "K"), True) or has_moved.get((color, "R", "kingside"), True):
            return False # King or rook has moved
        if board[king_row][5] is not None or board[king_row][6] is not None:
            return False # Squares between king and rook are not empty
        if is_in_check(board, color):
            return False # King is in check
        # Check if squares the king passes through are attacked
        for col in [4, 5, 6]:
            if is_square_attacked(board, (king_row, col), "b" if color == "w" else "w"):
                return False
        return True
    elif side == "queenside": 
        if has_moved.get((color, "K"), True) or has_moved.get((color, "R", "queenside"), True):
            return False # King or rook has moved
        if board[king_row][1] is not None or board[king_row][2] is not None or board[king_row][3] is not None:
            return False # Squares between king and rook are not empty
        if is_in_check(board, color):
            return False # King is in check
        # Check if squares the king passes through are attacked
        for col in [4, 3, 2]:
            if is_square_attacked(board, (king_row, col), "b" if color == "w" else "w"):
                return False
        return True

def make_castle(board, color, side):
    king_row = 7 if color == "w" else 0
    if side == "kingside":
        # king: col 4 -> col 6
        # rook: col 7 -> col 5
        board[king_row][6] = board[king_row][4]
        board[king_row][4] = None
        board[king_row][5] = board[king_row][7]
        board[king_row][7] = None
    else:  # queenside
        # king: col 4 -> col 2
        # rook: col 0 -> col 3
        board[king_row][2] = board[king_row][4]
        board[king_row][4] = None
        board[king_row][3] = board[king_row][0]
        board[king_row][0] = None