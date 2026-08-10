from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# TODO: the global game state dictionary goes here