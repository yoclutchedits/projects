from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chess_ai import get_groq_move
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()  # reads .env and puts its values into os.environ

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

from chess import (
    create_board, setup_pawns, setup_back_rank, is_move_safe, make_move,
    is_checkmate, is_stalemate, is_insufficient_material, is_in_check,
    find_king, is_castling_legal, make_castle, is_en_passant_safe, make_en_passant
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class MoveRequest(BaseModel):
    from_row: int
    from_col: int
    to_row: int
    to_col: int

class SquareRequest(BaseModel):
    row: int
    col: int

def new_game_state():
    board = create_board()
    setup_pawns(board)
    setup_back_rank(board)
    return {
        "board": board,
        "current_player": "w",
        "last_move": None,
        "has_moved": {
            ("w", "K"): False,
            ("b", "K"): False,
            ("w", "R", "kingside"): False,
            ("w", "R", "queenside"): False,
            ("b", "R", "kingside"): False,
            ("b", "R", "queenside"): False,
        },
        "move_history": [],
        "captured_pieces": [],
        "game_over": False,
        "status_message": "",
        "promotion_pending": None,
    }

def attempt_make_move(game_state,end,start, promote_to=None):
    if game_state["game_over"]:
        return {"success": False, "reason": "game_over", "message": "the game is over"}
    sr,sc = start
    piece = game_state["board"][sr][sc]
    if piece is None:
        return {"success": False, "reason": "illegal_move", "message": "please select a piece"}
    piece_color = piece[0]
    if piece_color != game_state["current_player"]:
        return {"success": False, "reason": "wrong_turn", "message": "it is not your turn"}
    if end == (start[0], start[1] + 2) and piece[1] == "K":
        is_legal = is_castling_legal(game_state["board"], piece_color, "kingside", game_state["has_moved"])
    elif end == (start[0], start[1] - 2) and piece[1] == "K":
        is_legal = is_castling_legal(game_state["board"], piece_color, "queenside", game_state["has_moved"])
    else:
        is_legal = is_move_safe(game_state["board"], start, end, piece_color) or is_en_passant_safe(game_state["board"], start, end,game_state["last_move"], piece_color)
    if not is_legal:
        return {"success": False, "reason": "illegal_move", "message": "that move is not legal"}
    is_ep = (
        piece is not None
        and piece[1] == "P"
        and is_en_passant_safe(game_state["board"], start, end, game_state["last_move"], piece_color)
    )
    if is_ep:
        captured=game_state["board"][sr][end[1]]
    else:
        captured=game_state["board"][end[0]][end[1]]
    if end == (start[0], start[1] + 2) and piece[1] == "K":
        castle_side = "kingside"
    elif end == (start[0], start[1] - 2) and piece[1] == "K":
        castle_side = "queenside"
    else:
        castle_side = None
    if castle_side is not None:
        make_castle(game_state["board"], piece_color, castle_side)
    elif is_ep:
        make_en_passant(game_state["board"], start, end)
    else:
        chosen = promote_to if promote_to in ("Q", "R", "B", "N") else "Q"
        make_move(game_state["board"], start, end, chosen)
    if piece[1] == "K":
        game_state["has_moved"][(piece_color, "K")] = True
    elif piece[1] == "R":
        if sc == 0:
            game_state["has_moved"][(piece_color, "R", "queenside")] = True
        elif sc == 7:
            game_state["has_moved"][(piece_color, "R", "kingside")] = True
    if captured:
        game_state["captured_pieces"].append(captured)
    game_state["move_history"].append(f"{piece}: {start} -> {end}")
    new_last_move = (start, end, piece)
    game_state["last_move"] = new_last_move
    next_player = "b" if piece_color == "w" else "w"
    game_state["current_player"] = next_player

    if is_checkmate(game_state["board"], next_player, new_last_move):
        game_state["status_message"] = "Checkmate!"
        game_state["game_over"] = True
    elif is_insufficient_material(game_state["board"]):
        game_state["status_message"] = "Draw — insufficient material!"
        game_state["game_over"] = True
    elif is_stalemate(game_state["board"], next_player, new_last_move):
        game_state["status_message"] = "Stalemate — it's a draw!"
        game_state["game_over"] = True
    elif is_in_check(game_state["board"], next_player):
        game_state["status_message"] = f"{'Black' if next_player == 'b' else 'White'} king is in check!"
    return {"success": True, "game_state": game_state}

# Single in-memory game — one game at a time, matches the original desktop app's design.
GAME_STATE = new_game_state()

def serialize_has_moved(has_moved):
    result = {}
    for key, value in has_moved.items():
        if len(key) == 2:
            color = key[0]
            string_key = color + "_king"  
        else:
            color = key[0]
            side = key[2]
            string_key = color + "_rook_" + side 
        result[string_key] = value
    return result

def serialize_game_state(state):
    return {
            "board": state["board"],
            "current_player": state["current_player"],
            "move_history": state["move_history"],
            "captured_pieces": state["captured_pieces"],
            "game_over": state["game_over"],
            "status_message": state["status_message"],
            "promotion_pending": state["promotion_pending"],
            "has_moved": serialize_has_moved(state["has_moved"]), 
            "last_move": state["last_move"],
        }
@app.get("/api/board")
def get_board():
    return serialize_game_state(GAME_STATE)
@app.post("/api/valid-moves")
def get_valid_moves_endpoint(square: SquareRequest):
    selected_square = (square.row, square.col)
    board = GAME_STATE["board"]
    current_player = GAME_STATE["current_player"]
    last_move = GAME_STATE["last_move"]
    has_moved = GAME_STATE["has_moved"]

    sr, sc = selected_square
    moving_piece = board[sr][sc]

    valid_moves = []

    if moving_piece is None:
        return {"valid_moves": valid_moves}

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

    return {"valid_moves": valid_moves}
@app.post("/api/move")
def make_move_endpoint(move: MoveRequest):
    start = (move.from_row, move.from_col)
    end = (move.to_row, move.to_col)
    result = attempt_make_move(GAME_STATE, end, start)
    return result
@app.post("/api/ai-move")
async def ai_move_endpoint():
    board = GAME_STATE["board"]
    current_player = GAME_STATE["current_player"]
    last_move = GAME_STATE["last_move"]
    has_moved = GAME_STATE["has_moved"]
    move_history = GAME_STATE["move_history"]
    move_count_before = len(GAME_STATE["move_history"])

    loop = asyncio.get_event_loop()
    ai_move = await loop.run_in_executor(
        None, get_groq_move, board, current_player, last_move, move_history, GROQ_API_KEY, has_moved
    )

    if ai_move is None:
        return {"success": True, "game_state": GAME_STATE}

    if len(GAME_STATE["move_history"]) != move_count_before:
        return {"success": False, "reason": "board_changed", "message": "Board changed while AI was thinking."}

    start, end = ai_move
    return attempt_make_move(GAME_STATE, end, start)