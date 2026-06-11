"""Physical tic-tac-toe on a CNC gantry with a vacuum gripper.

Deck layout, Z heights, and CNC settings come from ``tools/cnc_config.yaml``.
Vacuum gripper settings (RPM, settle delays, offset) come from
``tools/vacuum_config.yaml``.

Workflow:
    1. Prompt for game mode: 1 player (vs Easy/Medium/Hard AI) or 2 players.
    2. On each move: read the cell from the player (or AI), find the next
       available piece in storage, pick it up (vacuum on, lift), drop it on the
       board cell (vacuum off, lift).
    3. After the game, optionally reset by returning every placed piece to its
       storage well in reverse order.

Storage is two halves of a 15-well rack:
    columns 1-2 → O pieces, columns 4-5 → X pieces.
The 3x3 game board occupies columns 2-4 of a second 15-well rack.
"""

import sys
from pathlib import Path

import yaml
from cnc_machine_core import CNC_Machine, Deck, DeckState

# Make sibling `tools/` package importable when run as a script
DEMO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_ROOT))

from tools.vacuum_gripper import VacuumGripper  # noqa: E402
from game_logic import (  # noqa: E402
    AI_LEVELS,
    BOARD_WELL_MAP,
    STORAGE_WELLS,
    board_label,
    check_winner,
    display_board,
    is_draw,
    new_board,
    parse_input,
)

# --- Paths ---
TOOLS_DIR = DEMO_ROOT / "tools"
CNC_CONFIG_PATH = TOOLS_DIR / "cnc_config.yaml"
VACUUM_CONFIG_PATH = TOOLS_DIR / "vacuum_config.yaml"
PRESET_PATH = DEMO_ROOT / "presets" / "ttt_preset.yaml"
STATE_OUTPUT = DEMO_ROOT / "output" / "deck_state.yaml"
LABWARE_DIR = DEMO_ROOT / "custom_labware"
STORAGE_LABWARE = LABWARE_DIR / "storage_15_tuberack_100ul.json"
GAMEBOARD_LABWARE = LABWARE_DIR / "gameboard_15_tuberack_100ul.json"


# --- Load configs ---
with open(CNC_CONFIG_PATH, "r", encoding="utf-8") as _f:
    CNC_CFG = yaml.safe_load(_f)
with open(VACUUM_CONFIG_PATH, "r", encoding="utf-8") as _f:
    VAC_CFG = yaml.safe_load(_f)

VIRTUAL = CNC_CFG.get("virtual", False)
MOVE_SPEED = CNC_CFG.get("move_speed", 2500)

_Z = CNC_CFG["z_heights"]
Z_HOVER = _Z["hover"]
Z_PICK = _Z["pick"]
Z_PLACE = _Z["place"]

_DECK = CNC_CFG["deck"]
DECK_DEFINITION = _DECK.get("definition")
_SLOTS = _DECK["slots"]
SLOT_STORAGE = _SLOTS["storage"]
SLOT_BOARD = _SLOTS["gameboard"]


# ── CNC helpers ─────────────────────────────────────────────────────────


def get_well_xy(deck, slot, well_name, offset):
    """Absolute XY with gripper offset for a well. Z is supplied per-action."""
    x, y, _ = deck.get_labware(slot)[well_name].position(offset=offset)
    return x, y


def pick_and_place(cnc, gripper, deck, storage_well, board_well, offset):
    """Pick a piece from storage and place it on the game board."""
    sx, sy = get_well_xy(deck, SLOT_STORAGE, storage_well, offset)
    bx, by = get_well_xy(deck, SLOT_BOARD, board_well, offset)

    cnc.move_to_point_safe(sx, sy, Z_PICK, speed=MOVE_SPEED)
    gripper.engage()
    cnc.move_to_point_safe(bx, by, Z_PLACE, speed=MOVE_SPEED)
    gripper.release()


def return_piece(cnc, gripper, deck, board_well, storage_well, offset):
    """Pick a piece from the board and return it to storage."""
    bx, by = get_well_xy(deck, SLOT_BOARD, board_well, offset)
    sx, sy = get_well_xy(deck, SLOT_STORAGE, storage_well, offset)

    cnc.move_to_point_safe(bx, by, Z_PICK, speed=MOVE_SPEED)
    gripper.engage()
    cnc.move_to_point_safe(sx, sy, Z_PLACE, speed=MOVE_SPEED)
    gripper.release()


# ── Game helpers ────────────────────────────────────────────────────────


def load_preset():
    with open(PRESET_PATH, "r", encoding="utf-8") as f:
        preset = yaml.safe_load(f)
    state = DeckState(state_file=str(STATE_OUTPUT))
    state.init_from_preset(preset)
    return state


def get_next_storage_well(state, piece):
    for well in STORAGE_WELLS[piece]:
        if state.get_status(SLOT_STORAGE, well) == f"{piece}_piece":
            return well
    return None


def reset_board(cnc, gripper, deck, state, board, move_history, offset):
    if not move_history:
        return
    print("\nResetting board...")
    for piece, storage_well, board_well in reversed(move_history):
        print(f"  {piece}: board {board_well} -> storage {storage_well}")
        if not VIRTUAL:
            return_piece(cnc, gripper, deck, board_well, storage_well, offset)
        state.set_status(SLOT_BOARD, board_well, "empty")
        state.set_status(SLOT_STORAGE, storage_well, f"{piece}_piece")
    for r in range(3):
        for c in range(3):
            board[r][c] = None
    move_history.clear()
    print("Done.\n")


# ── UI ──────────────────────────────────────────────────────────────────


def select_mode():
    print("\n==============================")
    print("      CNC  TIC-TAC-TOE       ")
    print("==============================")
    print("\nGame Mode:")
    print("  1) 1 Player (vs AI)")
    print("  2) 2 Players")
    while True:
        choice = input("\nSelect (1/2): ").strip()
        if choice in ("1", "2"):
            break
        print("Invalid.")

    num_players = int(choice)
    human_symbol = None
    ai_difficulty = None

    if num_players == 1:
        print("\nYour symbol:")
        print("  O (goes first)")
        print("  X (goes second)")
        while True:
            sym = input("Choose (X/O): ").strip().upper()
            if sym in ("X", "O"):
                human_symbol = sym
                break
            print("Invalid.")

        print("\nDifficulty:")
        print("  1) Easy   - random moves")
        print("  2) Medium - blocks + random")
        print("  3) Hard   - unbeatable")
        while True:
            d = input("Choose (1/2/3): ").strip()
            if d in ("1", "2", "3"):
                ai_difficulty = ["easy", "medium", "hard"][int(d) - 1]
                break
            print("Invalid.")

    return num_players, human_symbol, ai_difficulty


def _confirm_quit(cnc, gripper, deck, state, board, move_history, offset):
    """Ask whether to reset before quitting. Returns False (quit signal)."""
    if move_history:
        while True:
            choice = input("Reset board before quitting? (y/n): ").strip().lower()
            if choice in ("y", "yes"):
                reset_board(cnc, gripper, deck, state, board, move_history, offset)
                break
            if choice in ("n", "no"):
                print("Board left as-is.")
                break
            print("Invalid.")
    return False


def play_game(cnc, gripper, deck, offset):
    """Run one game. Returns True to play again, False to quit."""
    num_players, human_symbol, ai_difficulty = select_mode()

    state = load_preset()
    board = new_board()
    move_history = []
    current = "O"

    if num_players == 1:
        ai_symbol = "O" if human_symbol == "X" else "X"
        ai_fn = AI_LEVELS[ai_difficulty]
        print(f"\nYou: {human_symbol}  |  AI: {ai_symbol} ({ai_difficulty})")
    else:
        ai_symbol = None
        ai_fn = None
        print("\nPlayer 1: X  |  Player 2: O")

    print("Moves: A1-C3 | 'reset' | 'quit'\n")

    while True:
        display_board(board)

        winner = check_winner(board)
        if winner:
            if num_players == 1:
                msg = "You win!" if winner == human_symbol else "AI wins!"
            else:
                msg = f"Player {'1' if winner == 'X' else '2'} ({winner}) wins!"
            print(msg)
            break

        if is_draw(board):
            print("Draw!")
            break

        is_ai_turn = num_players == 1 and current == ai_symbol

        if is_ai_turn:
            print(f"AI ({current}) thinking...")
            row, col = ai_fn(board, current)
            print(f"AI plays: {board_label(row, col)}")
        else:
            if num_players == 1:
                prompt = f"Your move ({current}): "
            else:
                prompt = f"Player {'1' if current == 'X' else '2'} ({current}): "

            while True:
                text = input(prompt).strip()
                if text.lower() == "quit":
                    return _confirm_quit(
                        cnc, gripper, deck, state, board, move_history, offset
                    )
                if text.lower() == "reset":
                    reset_board(cnc, gripper, deck, state, board, move_history, offset)
                    return True
                pos = parse_input(text)
                if pos is None:
                    print("Invalid. Use A1-C3.")
                    continue
                row, col = pos
                if board[row][col] is not None:
                    print("Occupied. Try again.")
                    continue
                break

        storage_well = get_next_storage_well(state, current)
        if storage_well is None:
            print(f"No {current} pieces left in storage!")
            break

        board_well = BOARD_WELL_MAP[(row, col)]

        if not VIRTUAL:
            pick_and_place(cnc, gripper, deck, storage_well, board_well, offset)
        else:
            print(
                f"  [VIRTUAL] {current}: storage {storage_well} -> board {board_well}"
            )

        board[row][col] = current
        state.set_status(SLOT_STORAGE, storage_well, "empty")
        state.set_status(SLOT_BOARD, board_well, current)
        move_history.append((current, storage_well, board_well))

        current = "O" if current == "X" else "X"

    # Post-game
    while True:
        choice = input("\n(p)lay again / (q)uit: ").strip().lower()
        if choice in ("p", "play"):
            reset_board(cnc, gripper, deck, state, board, move_history, offset)
            return True
        if choice in ("q", "quit"):
            return _confirm_quit(
                cnc, gripper, deck, state, board, move_history, offset
            )
        print("Invalid.")


# ── Main ────────────────────────────────────────────────────────────────


def main():
    cnc = CNC_Machine.from_config(CNC_CONFIG_PATH)
    cnc.connect()
    if not VIRTUAL:
        cnc.home()

    deck = Deck(DECK_DEFINITION) if DECK_DEFINITION else Deck()
    deck.load_labware(SLOT_STORAGE, str(STORAGE_LABWARE))
    deck.load_labware(SLOT_BOARD, str(GAMEBOARD_LABWARE))

    gripper = VacuumGripper(
        cnc=cnc,
        virtual=VIRTUAL,
        vacuum_rpm=VAC_CFG.get("vacuum_rpm", 2500),
        grip_delay_s=VAC_CFG.get("grip_delay_s", 0.5),
        place_delay_s=VAC_CFG.get("place_delay_s", 3.5),
        offset=VAC_CFG.get("offset", {"x": 0.0, "y": 0.0, "z": 0.0}),
    )
    gripper.connect()
    offset = gripper.offset

    try:
        playing = True
        while playing:
            playing = play_game(cnc, gripper, deck, offset)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        gripper.close()
        if not VIRTUAL:
            cnc.move_to_point_safe(0, 0, 0, speed=MOVE_SPEED)
        cnc.close()


main()
