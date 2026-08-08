from groq import Groq
import threading
import random
from keys import g_key
'''this is the key for the groq, which is used for AI moves
input the key in the below line, and don't forget to uncomment the line below'''
#g_key="your_key_here"
import pygame

from chess import (
    create_board, is_insufficient_material, setup_pawns, setup_back_rank, 
    is_move_safe, make_move, is_stalemate, is_checkmate, is_in_check, 
    find_king, make_en_passant, is_en_passant_safe, is_castling_legal, make_castle
)

pygame.init()

board = create_board()

setup_pawns(board)

setup_back_rank(board)

pygame.mixer.init()

SIDEBAR_WIDTH = 250


SQUARE_SIZE = 60

BOARD_SIZE = 8 * SQUARE_SIZE

SCREEN_WIDTH = 1000

SCREEN_HEIGHT = 700

BOARD_ORIGIN_X = (SCREEN_WIDTH - BOARD_SIZE) // 2

BOARD_ORIGIN_Y = (SCREEN_HEIGHT - BOARD_SIZE) // 2

SIDEBAR_X = BOARD_ORIGIN_X + BOARD_SIZE + 30


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Chess with Move Guides")

LIGHT = (240, 217, 181)

DARK = (181, 136, 99)

DOT_COLOR = (100, 110, 120)

CAPTURE_COLOR = (220, 60, 60)

BORDER_COLOR = (255, 255, 255)

BORDER_WIDTH = 4

client = Groq(api_key=g_key)

FONT = pygame.font.SysFont("arial", 24)

clock = pygame.time.Clock()

capture_sfx=pygame.mixer.Sound("projects/sfx/Capture.mp3")

check_sfx=pygame.mixer.Sound("projects/sfx/Check.mp3")

checkmate_sfx=pygame.mixer.Sound("projects/sfx/Checkmate.mp3")

move_sfx=pygame.mixer.Sound("projects/sfx/Move.mp3")

defeat_sfx=pygame.mixer.Sound("projects/sfx/Defeat.mp3")

victory_sfx=pygame.mixer.Sound("projects/sfx/Victory.mp3")

error_sfx=pygame.mixer.Sound("projects/sfx/Error.mp3")

PIECE_IMAGES = {}



def get_all_legal_moves_for_player(board, color, last_move):
    legal_moves = []
    for sr in range(8):
        for sc in range(8):
            piece = board[sr][sc]
            if piece and piece[0] == color:
                start = (sr, sc)
                moves = get_valid_moves(start, color, last_move)
                for end in moves:
                    legal_moves.append((start, end))
    return legal_moves

def get_groq_move(board, color, last_move, history):
    legal_moves = get_all_legal_moves_for_player(board, color, last_move)
    if not legal_moves:
        return None

    moves_str = ", ".join([
        f"{m[0]},{m[1]}->{m[2][0]},{m[2][1]}"
        for m in [(start[0], start[1], end) for start, end in legal_moves]
    ])
    board_str = "\n".join(
        [" ".join([cell if cell else ".." for cell in row]) for row in board]
    )

    # Show the last 10 moves for immediate tactical context
    recent_history = "\n".join(history[-10:]) if history else "Game started."

    prompt = f"""You are playing chess as Black ('b'). 

    Recent move history:
    {recent_history}

    Current board state (row 0 is Black's back rank, row 7 is White's back rank):
    {board_str}

    List of legal moves formatted as sr,sc->er,ec:
    {moves_str}

    Analyze the sequence of moves and current position to evaluate tactical plans.
    Select the single best move from the legal moves list "the best move dont go easy".
    Respond ONLY with the move in format 'sr,sc->er,ec' without any extra text or explanation."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        move_text = response.choices[0].message.content.strip()
        start_part, end_part = move_text.split("->")
        sr, sc = map(int, start_part.split(","))
        er, ec = map(int, end_part.split(","))

        chosen_move = ((sr, sc), (er, ec))
        if chosen_move in legal_moves:
            return chosen_move
    except Exception as e:
        print(f"Groq API error ({e}), picking fallback move.")

    return random.choice(legal_moves)

play_again_button_rect = None

def draw_turn_indicator():
    text = f"Turn: {'White' if current_player == 'w' else 'Black'}"
    turn_text = FONT.render(text, True, (255, 255, 255))
    screen.blit(turn_text, (SIDEBAR_X, BOARD_ORIGIN_Y))

def auto_scroll_history():
    global history_scroll
    item_height = 22
    container_h = 280
    total_content_height = len(move_history) * item_height
    history_scroll = max(0, total_content_height - container_h)

def draw_move_history():
    global history_scroll

    header = FONT.render("Move History", True, (255, 255, 255))
    screen.blit(header, (SIDEBAR_X, BOARD_ORIGIN_Y + 40))

    # Bounding box for move text
    container_x = SIDEBAR_X
    container_y = BOARD_ORIGIN_Y + 75
    container_w = SIDEBAR_WIDTH
    container_h = 280  # Keeps moves above the Captured section

    clip_rect = pygame.Rect(container_x, container_y, container_w, container_h)

    item_height = 22
    total_content_height = len(move_history) * item_height

    # Restrict scroll offset to valid bounds
    max_scroll = max(0, total_content_height - container_h)
    history_scroll = max(0, min(history_scroll, max_scroll))

    # Clip screen rendering to the move list box
    screen.set_clip(clip_rect)

    y_offset = container_y - history_scroll
    for move in move_history:
        if container_y - item_height <= y_offset <= container_y + container_h:
            move_text = FONT.render(move, True, (200, 200, 200))
            screen.blit(move_text, (container_x, y_offset))
        y_offset += item_height

    # Restore normal full-screen drawing
    screen.set_clip(None)

def square_to_notation(square):
    row, col = square
    return f"{chr(ord('a') + col)}{8 - row}"

move_history = []

def reset_game():
    global board, current_player, selected_square, valid_moves, error_message, play_again_button_rect
    global game_over, promotion_pending, king_in_check_square, last_move, has_moved, board_flipped, mode_selected
    global ai_thinking, ai_chosen_move
    global move_history,captured_pieces,history_scroll
    move_history = []
    board = create_board()
    history_scroll = 0
    captured_pieces = []
    setup_pawns(board)
    setup_back_rank(board)
    current_player = "w"
    selected_square = None
    valid_moves = []
    error_message = ""
    game_over = False
    promotion_pending = None
    king_in_check_square = None
    last_move = None
    ai_thinking = False
    ai_chosen_move = None
    board_flipped = False
    mode_selected = False  # Triggers mode selection menu on reset
    has_moved = {
        ("w", "K"): False,
        ("b", "K"): False,
        ("w", "R", "kingside"): False,
        ("w", "R", "queenside"): False,
        ("b", "R", "kingside"): False,
        ("b", "R", "queenside"): False,
    }
    play_again_button_rect = None

def draw_play_again_button():
    if not game_over:
        return
    button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 100, 160, 40)
    pygame.draw.rect(screen, (60, 60, 60), button_rect)
    pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)
    text = FONT.render("Play Again", True, (255, 255, 255))
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)
    return button_rect

def draw_cordinates():
    for i in range(8):
        row_number = 8 - i if not board_flipped else i + 1
        row_text = FONT.render(str(row_number), True, (255, 255, 255))
        screen.blit(row_text, (BOARD_ORIGIN_X - row_text.get_width() - 8, BOARD_ORIGIN_Y + i * SQUARE_SIZE + SQUARE_SIZE // 2 - row_text.get_height() // 2))
        col_letter = chr(ord('a') + i) if not board_flipped else chr(ord('h') - i)
        col_text = FONT.render(col_letter, True, (255, 255, 255))
        screen.blit(col_text, (BOARD_ORIGIN_X + i * SQUARE_SIZE + SQUARE_SIZE // 2 - col_text.get_width() // 2, BOARD_ORIGIN_Y + BOARD_SIZE + 8))

def load_piece_images():
    piece_codes = ["wK", "wQ", "wR", "wB", "wN", "wP",
                "bK", "bQ", "bR", "bB", "bN", "bP"]
    for code in piece_codes:
        image = pygame.image.load(f"projects/pieces/{code}.png")
        image = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
        PIECE_IMAGES[code] = image

def draw_choose_ai_or_human():
    prompt_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50, 300, 100)
    pygame.draw.rect(screen, (50, 50, 50), prompt_rect)
    pygame.draw.rect(screen, (255, 255, 255), prompt_rect, 2)

    text = FONT.render("Play against AI?", True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
    screen.blit(text, text_rect)

    ai_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 10, 100, 30)
    human_button_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 + 10, 100, 30)
    pygame.draw.rect(screen, (100, 100, 100), ai_button_rect)
    pygame.draw.rect(screen, (100, 100, 100), human_button_rect)
    ai_text = FONT.render("AI", True, (255, 255, 255))
    human_text = FONT.render("Human", True, (255, 255, 255))
    screen.blit(ai_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 15))
    screen.blit(human_text, (SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 15))

def draw_board():
    for row in range(8):
        for col in range(8):
            color = LIGHT if (row + col) % 2 == 0 else DARK
            x, y = to_screen_coords(row, col)
            pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    board_rect = pygame.Rect(BOARD_ORIGIN_X, BOARD_ORIGIN_Y, BOARD_SIZE, BOARD_SIZE)
    pygame.draw.rect(screen, BORDER_COLOR, board_rect, BORDER_WIDTH)

def draw_check_indicator(king_in_check_square):
        if king_in_check_square is not None:
            row, col = king_in_check_square
            x, y = to_screen_coords(row, col)
            pygame.draw.rect(screen, (255, 0, 0), (x, y, SQUARE_SIZE, SQUARE_SIZE), 5)


def get_valid_moves(selected_square, current_player, last_move):
    if selected_square is None:
        return []

    valid_moves = []
    sr, sc = selected_square
    moving_piece = board[sr][sc]

    for r in range(8):
        for c in range(8):
            target = (r, c)
            if is_move_safe(board, selected_square, target, current_player):
                valid_moves.append(target)
            elif moving_piece and moving_piece[1] == "P":
                if is_en_passant_safe(board, selected_square, target, last_move, current_player):
                    valid_moves.append(target)

    if moving_piece and moving_piece[1] == "K":
        if is_castling_legal(board, current_player, "kingside", has_moved):
            valid_moves.append((sr, sc + 2))
        if is_castling_legal(board, current_player, "queenside", has_moved):
            valid_moves.append((sr, sc - 2))

    return valid_moves

def draw_valid_moves(valid_moves, selected_square=None, last_move=None):
    for row, col in valid_moves:
        x, y = to_screen_coords(row, col)
        center_x = x + SQUARE_SIZE // 2
        center_y = y + SQUARE_SIZE // 2
        target_piece = board[row][col]
        is_ep = False
        if selected_square:
            sr, sc = selected_square
            p = board[sr][sc]
            if p and p[1] == "P" and is_en_passant_safe(board, selected_square, (row, col), last_move, p[0]):
                is_ep = True

        mover = board[selected_square[0]][selected_square[1]] if selected_square else None
        is_enemy_piece = target_piece is not None and mover is not None and target_piece[0] != mover[0]

        if is_enemy_piece or is_ep:
            pygame.draw.circle(screen, CAPTURE_COLOR, (center_x, center_y), SQUARE_SIZE // 2 - 4, 4)
        else:
            pygame.draw.circle(screen, DOT_COLOR, (center_x, center_y), SQUARE_SIZE // 6)

def draw_selected(selected_square):
    if selected_square is not None:
        row, col = selected_square
        x, y = to_screen_coords(row, col)
        pygame.draw.rect(
            screen,
            (255, 255, 0),
            (x, y, SQUARE_SIZE, SQUARE_SIZE),
            4
        )

def draw_message(message):
    if message:
        text = FONT.render(message, True, (255, 255, 255))
        bg_rect = pygame.Rect(10, SCREEN_HEIGHT - 35, text.get_width() + 10, 30)
        pygame.draw.rect(screen, (200, 0, 0), bg_rect)
        screen.blit(text, (15, SCREEN_HEIGHT - 32))

def draw_promotion_prompt():
    if promotion_pending is None:
        return
    row, col, color = promotion_pending
    base_x, base_y = to_screen_coords(row, col)
    direction = 1 if color == "w" else -1
    if board_flipped:
        direction = -direction
    choices = ["Q", "R", "B", "N"]
    for i, choice in enumerate(choices):
        piece_code = color + choice
        image = PIECE_IMAGES[piece_code]
        y = base_y + i * SQUARE_SIZE * direction
        pygame.draw.rect(screen, (50, 50, 50), (base_x, y, SQUARE_SIZE, SQUARE_SIZE))
        screen.blit(image, (base_x, y))

def draw_pieces(board):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece is not None:
                image = PIECE_IMAGES[piece]
                x, y = to_screen_coords(row, col)
                screen.blit(image, (x, y))

def to_screen_coords(row, col):
    if board_flipped:
        row = 7 - row
        col = 7 - col
    x = BOARD_ORIGIN_X + col * SQUARE_SIZE
    y = BOARD_ORIGIN_Y + row * SQUARE_SIZE
    return x, y

def fetch_ai_move_async(board_copy, color, last_move_copy, history_copy):
    global ai_chosen_move, ai_thinking
    ai_chosen_move = get_groq_move(board_copy, color, last_move_copy, history_copy)
    ai_thinking = False

def draw_captured_pieces():
    white_captured = [p for p in captured_pieces if p[0] == "w"]
    black_captured = [p for p in captured_pieces if p[0] == "b"]
    header = FONT.render("Captured:", True, (255, 255, 255))
    screen.blit(header, (SIDEBAR_X, BOARD_ORIGIN_Y + BOARD_SIZE - 100))
    w_text = FONT.render("White: " + " ".join(white_captured), True, (200, 200, 200))
    b_text = FONT.render("Black: " + " ".join(black_captured), True, (200, 200, 200))
    screen.blit(w_text, (SIDEBAR_X, BOARD_ORIGIN_Y + BOARD_SIZE - 70))
    screen.blit(b_text, (SIDEBAR_X, BOARD_ORIGIN_Y + BOARD_SIZE - 45))

white_time = 600  # seconds (10 minutes)

black_time = 600

running = True

selected_square = None

valid_moves = []

ai_mode=False 

ai_selection_pending=False

current_player = "w"

error_message = ""

board_flipped = False

mode_selected = False  # Triggers mode selection menu on reset

play_error_sfx = False

game_over = False

promotion_pending = None

king_in_check_square = None

last_move = None

ai_thinking = False

ai_chosen_move = None

history_scroll = 0

captured_pieces = []
has_moved = {
    ("w", "K"): False, ("b", "K"): False,
    ("w", "R", "kingside"): False, ("w", "R", "queenside"): False,
    ("b", "R", "kingside"): False, ("b", "R", "queenside"): False,
}

play_again_button_rect = None
# Preload piece images ONCE outside the loop during setup
load_piece_images()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEWHEEL:
            # Scroll up/down over move history
            history_scroll -= event.y * 20
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not mode_selected:
                x, y = event.pos
                # AI Button bounds
                if (SCREEN_WIDTH // 2 - 120 <= x <= SCREEN_WIDTH // 2 - 20 and SCREEN_HEIGHT // 2 + 10 <= y <= SCREEN_HEIGHT // 2 + 40):
                    ai_mode = True
                    mode_selected = True
                    continue
                # Human Button bounds
                elif (SCREEN_WIDTH // 2 + 20 <= x <= SCREEN_WIDTH // 2 + 120 and SCREEN_HEIGHT // 2 + 10 <= y <= SCREEN_HEIGHT // 2 + 40):
                    ai_mode = False
                    mode_selected = True
                    continue
        
            if game_over:
                if (play_again_button_rect is not None and play_again_button_rect.collidepoint(event.pos)):
                    reset_game()
            else:
                x, y = event.pos
                board_x = x - BOARD_ORIGIN_X
                board_y = y - BOARD_ORIGIN_Y
                if not (0 <= board_x < BOARD_SIZE and 0 <= board_y < BOARD_SIZE):
                    continue
                col = board_x // SQUARE_SIZE
                row = board_y // SQUARE_SIZE
                if board_flipped:
                    row = 7 - row
                    col = 7 - col
                clicked = (row, col)
                
                if promotion_pending is not None:
                    prom_row, prom_col, prom_color = promotion_pending
                    direction = 1 if prom_color == "w" else -1
                    if board_flipped:
                        direction = -direction
                    if clicked[1] == prom_col:
                        for i in range(4):
                            target_row = prom_row + i * direction
                            if clicked[0] == target_row:
                                promote_to = ["Q", "R", "B", "N"][i]
                                board[prom_row][prom_col] = prom_color + promote_to
                                promotion_pending = None
                                current_player = "b" if current_player == "w" else "w"
                                if ai_mode != True:
                                    board_flipped = (current_player == "b")
                                king_in_check = is_in_check(board, current_player) if not game_over else False
                                if king_in_check:
                                    king_in_check_square = find_king(board, current_player)
                                else:
                                    king_in_check_square = None
                                if is_checkmate(board, current_player, last_move):
                                    error_message = f"Checkmate! {'Black' if current_player == 'w' else 'White'} wins!"
                                    checkmate_sfx.play()
                                    victory_sfx.play()
                                    game_over = True
                                elif is_insufficient_material(board):
                                    error_message = "Draw — insufficient material!"
                                    defeat_sfx.play()
                                    game_over = True
                                elif is_stalemate(board, current_player, last_move):
                                    error_message = "Stalemate — it's a draw!"
                                    defeat_sfx.play()
                                    game_over = True
                                break
                elif ai_selection_pending:
                    if clicked == ai_selection_pending[1]:
                        moving_piece = board[ai_selection_pending[0][0]][ai_selection_pending[0][1]]
                        is_ep = (
                            moving_piece is not None
                            and moving_piece[1] == "P"
                            and is_en_passant_safe(board, ai_selection_pending[0], clicked, last_move, current_player)
                        )
                        if is_ep or is_move_safe(board, ai_selection_pending[0], clicked, current_player):
                            was_capture = board[clicked[0]][clicked[1]] is not None or is_ep
                            captured = board[clicked[0]][clicked[1]] if not is_ep else board[selected_square[0]][clicked[1]]
                            if is_ep:
                                make_en_passant(board, ai_selection_pending[0], clicked)
                                move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(ai_selection_pending[0])} -> {square_to_notation(clicked)}")
                            else:
                                make_move(board, ai_selection_pending[0], clicked, promote_to="Q")
                                move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(ai_selection_pending[0])} -> {square_to_notation(clicked)}")
                            if was_capture:
                                capture_sfx.play()
                                if captured:
                                    captured_pieces.append(captured)
                                    auto_scroll_history()
                            else:
                                move_sfx.play()
                            error_message = ""
                            if moving_piece[1] == "K":
                                has_moved[(current_player, "K")] = True
                            elif moving_piece[1] == "R":
                                start_col = ai_selection_pending[0][1]
                                if start_col == 0:
                                    has_moved[(current_player, "R", "queenside")] = True
                                elif start_col == 7:
                                    has_moved[(current_player, "R", "kingside")] = True
                            last_move = (ai_selection_pending[0], clicked, moving_piece)
                            if moving_piece[1] == "P" and (clicked[0] == 0 or clicked[0] == 7):
                                promotion_pending = (clicked[0], clicked[1], moving_piece[0])
                            else:
                                current_player = "b" if current_player == "w" else "w"
                                if ai_mode != True:
                                    board_flipped = (current_player == "b")
                                king_in_check = is_in_check(board, current_player) if not game_over else False
                                if king_in_check:
                                    king_in_check_square = find_king(board, current_player)
                                else:
                                    king_in_check_square = None
                                if is_checkmate(board, current_player, last_move):
                                    error_message = f"Checkmate! {'Black' if current_player == 'w' else 'White'} wins!"
                                    checkmate_sfx.play()
                                    victory_sfx.play()
                                    game_over = True
                                elif is_insufficient_material(board):
                                    error_message = "Draw — insufficient material!"
                                    defeat_sfx.play()
                                    game_over = True
                                elif is_stalemate(board, current_player, last_move):
                                    error_message = "Stalemate — it's a draw!"
                                    defeat_sfx.play()
                                    game_over = True
                            ai_selection_pending = False
                
                try:
                    piece_at_click = board[row][col]
                except IndexError:
                    continue

                if selected_square is None:
                    if piece_at_click is not None and piece_at_click[0] == current_player:
                        selected_square = clicked
                        valid_moves = get_valid_moves(selected_square, current_player, last_move)
                        error_message = ""
                else:
                    if clicked == selected_square:
                        selected_square = None
                        valid_moves = []
                    elif piece_at_click is not None and piece_at_click[0] == current_player:
                        selected_square = clicked
                        valid_moves = get_valid_moves(selected_square, current_player, last_move)
                        error_message = ""
                    else:
                        moving_piece = board[selected_square[0]][selected_square[1]]
                        is_ep = (
                            moving_piece is not None
                            and moving_piece[1] == "P"
                            and is_en_passant_safe(board, selected_square, clicked, last_move, current_player)
                        )
                        is_castle = False
                        castle_side = None
                        if moving_piece is not None and moving_piece[1] == "K":
                            if clicked == (selected_square[0], selected_square[1] + 2):
                                castle_side = "kingside"
                            elif clicked == (selected_square[0], selected_square[1] - 2):
                                castle_side = "queenside"
                            if castle_side is not None:
                                is_castle = is_castling_legal(board, current_player, castle_side, has_moved)
                        if is_castle:
                            make_castle(board, current_player, castle_side)
                            move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(selected_square)} -> {square_to_notation(clicked)}")
                            move_sfx.play()
                            error_message = ""
                            last_move = (selected_square, clicked, moving_piece)
                            current_player = "b" if current_player == "w" else "w"
                            if ai_mode != True:
                                board_flipped = (current_player == "b")
                            king_in_check = is_in_check(board, current_player) if not game_over else False
                            if king_in_check:
                                king_in_check_square = find_king(board, current_player)
                            else:
                                king_in_check_square = None
                            if is_checkmate(board, current_player, last_move):
                                error_message = f"Checkmate! {'Black' if current_player == 'w' else 'White'} wins!"
                                checkmate_sfx.play()
                                victory_sfx.play()
                                game_over = True
                            elif is_insufficient_material(board):
                                error_message = "Draw — insufficient material!"
                                defeat_sfx.play()
                                game_over = True
                            elif is_stalemate(board, current_player, last_move):
                                error_message = "Stalemate — it's a draw!"
                                defeat_sfx.play()
                                game_over = True
                            selected_square = None 
                            valid_moves = [] 
                        else:
                            is_standard_safe = is_move_safe(board, selected_square, clicked, current_player)
                            if is_ep or is_standard_safe:
                                was_capture = board[clicked[0]][clicked[1]] is not None or is_ep
                                captured = board[clicked[0]][clicked[1]] if not is_ep else board[selected_square[0]][clicked[1]]
                                if is_ep:
                                    make_en_passant(board, selected_square, clicked)
                                    move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(selected_square)} -> {square_to_notation(clicked)}")
                                else:
                                    make_move(board, selected_square, clicked, promote_to="Q")
                                    move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(selected_square)} -> {square_to_notation(clicked)}")
                                if was_capture:
                                    capture_sfx.play()
                                    if captured:
                                        captured_pieces.append(captured)
                                        auto_scroll_history()
                                else:
                                    move_sfx.play()
                                error_message = ""
                                if moving_piece[1] == "K":
                                    has_moved[(current_player, "K")] = True
                                elif moving_piece[1] == "R":
                                    start_col = selected_square[1]
                                    if start_col == 0:
                                        has_moved[(current_player, "R", "queenside")] = True
                                    elif start_col == 7:
                                        has_moved[(current_player, "R", "kingside")] = True
                                # Track the last move for En Passant validation
                                last_move = (selected_square, clicked, moving_piece)
                                if moving_piece[1] == "P" and (clicked[0] == 0 or clicked[0] == 7):
                                    promotion_pending = (clicked[0], clicked[1], moving_piece[0])
                                else:
                                    current_player = "b" if current_player == "w" else "w"
                                    if ai_mode != True:
                                        board_flipped = (current_player == "b")
                                    king_in_check = is_in_check(board, current_player) if not game_over else False
                                    if king_in_check:
                                        king_in_check_square = find_king(board, current_player)
                                    else:
                                        king_in_check_square = None
                                    if is_checkmate(board, current_player, last_move):
                                        error_message = f"Checkmate! {'Black' if current_player == 'w' else 'White'} wins!"
                                        checkmate_sfx.play()
                                        victory_sfx.play()
                                        game_over = True
                                    elif is_insufficient_material(board):
                                        error_message = "Draw — insufficient material!"
                                        play_error_sfx = True
                                        defeat_sfx.play()
                                        game_over = True
                                    elif is_stalemate(board, current_player, last_move):
                                        error_message = "Stalemate — it's a draw!"
                                        play_error_sfx = True
                                        defeat_sfx.play()
                                        game_over = True
                                    elif is_in_check(board, current_player):
                                        check_sfx.play()
                                        error_message = f"{'Black' if current_player == 'b' else 'White'} king is in check!"
                            else:
                                error_message = "Invalid move. Try again."
                                play_error_sfx = True
                            selected_square = None
                            valid_moves = []

# Async AI Move Execution (Runs outside event loop without blocking UI)
    if (
        ai_mode
        and mode_selected
        and current_player == "b"
        and not game_over
        and promotion_pending is None
    ):
        if not ai_thinking and ai_chosen_move is None:
            ai_thinking = True
            board_copy = [row[:] for row in board]
            threading.Thread(
                target=fetch_ai_move_async,
                args=(board_copy, "b", last_move, move_history[:]),
                daemon=True,
            ).start()

        if ai_chosen_move is not None:
            ai_move = ai_chosen_move
            ai_chosen_move = None

            start, end = ai_move
            moving_piece = board[start[0]][start[1]]

            is_ep = (
                moving_piece is not None
                and moving_piece[1] == "P"
                and is_en_passant_safe(board, start, end, last_move, "b")
            )
            castle_side = None
            if moving_piece and moving_piece[1] == "K":
                if end == (start[0], start[1] + 2):
                    castle_side = "kingside"
                elif end == (start[0], start[1] - 2):
                    castle_side = "queenside"

            if castle_side and is_castling_legal(board, "b", castle_side, has_moved):
                make_castle(board, "b", castle_side)
                move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(start)} -> {square_to_notation(end)}")
                move_sfx.play()
            elif is_ep:
                make_en_passant(board, start, end)
                move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(start)} -> {square_to_notation(end)}")
                capture_sfx.play()
            else:
                was_capture = board[end[0]][end[1]] is not None
                captured = board[clicked[0]][clicked[1]] if not is_ep else board[selected_square[0]][clicked[1]]
                make_move(board, start, end, promote_to="Q")
                if was_capture:
                    capture_sfx.play()
                    if captured:
                        captured_pieces.append(captured)
                        auto_scroll_history()
                else:
                    move_sfx.play()
                move_history.append(f"{'White' if current_player == 'w' else 'Black'} ({moving_piece}): {square_to_notation(start)} -> {square_to_notation(end)}")
            last_move = (start, end, moving_piece)
            current_player = "w"

            if is_in_check(board, current_player):
                king_in_check_square = find_king(board, current_player)
                check_sfx.play()
                error_message = "White king is in check!"
            else:
                king_in_check_square = None

            if is_checkmate(board, current_player, last_move):
                error_message = "Checkmate! Black wins!"
                checkmate_sfx.play()
                defeat_sfx.play()
                game_over = True
            elif is_insufficient_material(board):
                error_message = "Draw — insufficient material!"
                defeat_sfx.play()
                game_over = True
            elif is_stalemate(board, current_player, last_move):
                error_message = "Stalemate — it's a draw!"
                defeat_sfx.play()
                game_over = True

    # Render Section
    screen.fill((30, 30, 30))
    draw_board()
    draw_valid_moves(valid_moves, selected_square, last_move)
    draw_pieces(board)
    draw_cordinates()
    draw_selected(selected_square)
    draw_check_indicator(king_in_check_square)
    draw_message(error_message)
    draw_captured_pieces()

    if play_error_sfx:
        error_sfx.play()
        play_error_sfx = False

    draw_promotion_prompt()
    draw_turn_indicator()
    draw_move_history()
    if not mode_selected:
        draw_choose_ai_or_human()

    play_again_button_rect = draw_play_again_button()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()