import random
from groq import Groq
from chess import is_move_safe, is_en_passant_safe, is_castling_legal

def get_all_legal_moves_for_player(board, color, last_move, has_moved):
    legal_moves = []
    for sr in range(8):
        for sc in range(8):
            piece = board[sr][sc]
            if piece and piece[0] == color:
                start = (sr, sc)
                for er in range(8):
                    for ec in range(8):
                        end = (er, ec)
                        if is_move_safe(board, start, end, color):
                            legal_moves.append((start, end))
                        elif piece[1] == "P" and is_en_passant_safe(board, start, end, last_move, color):
                            legal_moves.append((start, end))
    return legal_moves

def get_groq_move(board, color, last_move, history, api_key,has_moved):
    client = Groq(api_key=api_key)
    legal_moves = get_all_legal_moves_for_player(board, color, last_move, has_moved)
    if not legal_moves:
        return None

    moves_str = ", ".join([f"{s[0]},{s[1]}->{e[0]},{e[1]}" for s, e in legal_moves])
    board_str = "\n".join([" ".join([cell if cell else ".." for cell in row]) for row in board])
    recent_history = "\n".join(history[-10:]) if history else "Game started."

    prompt = f"""You are playing chess as Black ('b').

Recent move history:
{recent_history}

Current board state (row 0 is Black's back rank, row 7 is White's back rank):
{board_str}

List of legal moves formatted as sr,sc->er,ec:
{moves_str}

Select the single best move from the legal moves list. Play well, don't go easy.
Respond ONLY with the move in format 'sr,sc->er,ec' without any extra text."""

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