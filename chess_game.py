'''add 
1)draw ✅,
2)stalemate✅,
2.5)checkmate✅,
8)en passant✅,
9)castling✅,
4)pygame prompt for pawn promotion✅,
3)custom visual icon for the pieces✅,
12)Ai,
13)a sidebar showing active player turn, captured pieces, and move history in standard algebraic notation,
7)Chess Clock (✅, but not fully implemented),disabled for now, will be added when the menu or sidebar is added, so that the player can choose to flip the board or not
6)Sound Effects✅,
10)Board Flipping(✅, but not fully implemented),
5)visual indicators for check and checkmate✅
14) add a main menu
11) when the game ends add a option to play a new game.
'''
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

SQUARE_SIZE = 60

BOARD_SIZE = 8 * SQUARE_SIZE

SCREEN_WIDTH = 1000

SCREEN_HEIGHT = 700

BOARD_ORIGIN_X = (SCREEN_WIDTH - BOARD_SIZE) // 2

BOARD_ORIGIN_Y = (SCREEN_HEIGHT - BOARD_SIZE) // 2

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption("Chess with Move Guides")

LIGHT = (240, 217, 181)

DARK = (181, 136, 99)

DOT_COLOR = (100, 110, 120)

CAPTURE_COLOR = (220, 60, 60)

BORDER_COLOR = (255, 255, 255)

BORDER_WIDTH = 4

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

def format_time(seconds):
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02}:{secs:02}"

def draw_clocks(white_time, black_time):
    white_text = FONT.render(f"White: {format_time(white_time)}", True, (255, 255, 255))
    black_text = FONT.render(f"Black: {format_time(black_time)}", True, (255, 255, 255))
    screen.blit(white_text, (BOARD_ORIGIN_X + BOARD_SIZE - 150, BOARD_ORIGIN_Y + 10))
    screen.blit(black_text, (BOARD_ORIGIN_X + BOARD_SIZE - 150, BOARD_ORIGIN_Y + 40))

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

white_time = 600  # seconds (10 minutes)

black_time = 600

running = True

selected_square = None

valid_moves = []

current_player = "w"

error_message = ""

board_flipped = False

play_error_sfx = False

game_over = False

promotion_pending = None

king_in_check_square = None

last_move = None

#last_tick = pygame.time.get_ticks()

has_moved = {
    ("w", "K"): False, ("b", "K"): False,
    ("w", "R", "kingside"): False, ("w", "R", "queenside"): False,
    ("b", "R", "kingside"): False, ("b", "R", "queenside"): False,
}

while running:
    for event in pygame.event.get():
        # add when we add the sidebar,to move the clocks to the sidebar, and start the clock as soon as the first move is made, and pause the clock when the game is over, and reset the clock when a new game starts
        '''now = pygame.time.get_ticks()
        elapsed = (now - last_tick) / 1000  # convert ms to seconds
        last_tick = now

        if not game_over:
            if current_player == "w":
                white_time -= elapsed
            else:
                black_time -= elapsed
        if white_time <= 0:
            error_message = "White ran out of time. Black wins!"
            game_over = True
        elif black_time <= 0:
            error_message = "Black ran out of time. White wins!"
            game_over = True'''
        '''if event.type == pygame.KEYDOWN:
                if board_flipped:
                    board_flipped = not board_flipped''' #disabled for now, will be added when the menu or sidebar is added, so that the player can choose to flip the board or not
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:

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
                            #board_flipped = (current_player == "b")
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
                        move_sfx.play()
                        error_message = ""
                        last_move = (selected_square, clicked, moving_piece)
                        current_player = "b" if current_player == "w" else "w"
                        #board_flipped = (current_player == "b")
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
                            if is_ep:
                                make_en_passant(board, selected_square, clicked)
                            else:
                                make_move(board, selected_square, clicked, promote_to="Q")
                            if was_capture:
                                capture_sfx.play()
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
                                #board_flipped = (current_player == "b")
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

    screen.fill((30, 30, 30))  # or any background color you like — dark gray shown here
    draw_board()
    load_piece_images()
    draw_valid_moves(valid_moves, selected_square, last_move)
    draw_pieces(board)
    draw_cordinates()
    draw_selected(selected_square)
    #draw_clocks(white_time, black_time)
    draw_message(error_message)
    if play_error_sfx:
        error_sfx.play()
        play_error_sfx = False
    draw_promotion_prompt()
    draw_check_indicator(king_in_check_square)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()