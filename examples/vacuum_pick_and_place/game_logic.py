"""Tic-tac-toe game logic, AI, and terminal display.

Pure Python — no CNC, no I/O. Imported by ``protocols/tic_tac_toe.py``.
"""

import random

# ── Board <-> Labware Mapping ───────────────────────────────────────────

# Board (row, col) -> labware well on the gameboard slot.
# The 3x3 play area occupies columns 2-4 of a 15-well rack (5 cols x 3 rows).
BOARD_WELL_MAP = {
    (0, 0): "A2", (0, 1): "A3", (0, 2): "A4",
    (1, 0): "B2", (1, 1): "B3", (1, 2): "B4",
    (2, 0): "C2", (2, 1): "C3", (2, 2): "C4",
}

WELL_TO_BOARD = {v: k for k, v in BOARD_WELL_MAP.items()}

# Storage well ordering for each piece type (consumed in this order).
# O pieces in columns 1-2, X pieces in columns 4-5 of the storage rack.
STORAGE_WELLS = {
    "O": ["A1", "B1", "C1", "A2", "B2", "C2"],
    "X": ["A4", "B4", "C4", "A5", "B5", "C5"],
}

# ── User Input Mapping ──────────────────────────────────────────────────

# Player types A1..C3 (1-indexed columns relative to the 3x3 board).
INPUT_MAP = {}
for _r, _letter in enumerate("ABC"):
    for _c, _digit in enumerate("123"):
        INPUT_MAP[f"{_letter}{_digit}"] = (_r, _c)


# ── Board Operations ────────────────────────────────────────────────────

def new_board():
    return [[None for _ in range(3)] for _ in range(3)]


def get_empty_cells(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]


def check_winner(board):
    lines = []
    for r in range(3):
        lines.append([(r, 0), (r, 1), (r, 2)])
    for c in range(3):
        lines.append([(0, c), (1, c), (2, c)])
    lines.append([(0, 0), (1, 1), (2, 2)])
    lines.append([(0, 2), (1, 1), (2, 0)])
    for line in lines:
        vals = [board[r][c] for r, c in line]
        if vals[0] is not None and vals[0] == vals[1] == vals[2]:
            return vals[0]
    return None


def is_draw(board):
    return not get_empty_cells(board) and check_winner(board) is None


def display_board(board):
    sym = {None: ".", "X": "X", "O": "O"}
    print()
    print("       1   2   3")
    print("     +---+---+---+")
    for r, letter in enumerate("ABC"):
        cells = " | ".join(sym[board[r][c]] for c in range(3))
        print(f"  {letter}  | {cells} |")
        print("     +---+---+---+")
    print()


def parse_input(text):
    return INPUT_MAP.get(text.strip().upper())


def board_label(row, col):
    return f"{'ABC'[row]}{col + 1}"


# ── AI ──────────────────────────────────────────────────────────────────

def ai_easy(board, symbol):
    """Pick a random empty cell."""
    return random.choice(get_empty_cells(board))


def _find_winning_move(board, symbol):
    """Return (row, col) that wins for *symbol*, or None."""
    for r, c in get_empty_cells(board):
        board[r][c] = symbol
        if check_winner(board) == symbol:
            board[r][c] = None
            return (r, c)
        board[r][c] = None
    return None


def ai_medium(board, symbol):
    """Win if possible, block opponent's win, otherwise random."""
    opponent = "O" if symbol == "X" else "X"
    move = _find_winning_move(board, symbol)
    if move:
        return move
    move = _find_winning_move(board, opponent)
    if move:
        return move
    return random.choice(get_empty_cells(board))


def _minimax(board, is_maximizing, ai_sym, opp_sym, alpha, beta):
    winner = check_winner(board)
    if winner == ai_sym:
        return 10
    if winner == opp_sym:
        return -10
    if not get_empty_cells(board):
        return 0
    if is_maximizing:
        best = -100
        for r, c in get_empty_cells(board):
            board[r][c] = ai_sym
            score = _minimax(board, False, ai_sym, opp_sym, alpha, beta)
            board[r][c] = None
            best = max(best, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best
    else:
        best = 100
        for r, c in get_empty_cells(board):
            board[r][c] = opp_sym
            score = _minimax(board, True, ai_sym, opp_sym, alpha, beta)
            board[r][c] = None
            best = min(best, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best


def ai_hard(board, symbol):
    """Minimax with alpha-beta pruning (unbeatable)."""
    opponent = "O" if symbol == "X" else "X"
    best_score = -100
    best_move = None
    for r, c in get_empty_cells(board):
        board[r][c] = symbol
        score = _minimax(board, False, symbol, opponent, -100, 100)
        board[r][c] = None
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return best_move


AI_LEVELS = {
    "easy": ai_easy,
    "medium": ai_medium,
    "hard": ai_hard,
}
