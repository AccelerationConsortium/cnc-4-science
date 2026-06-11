"""CLI tic-tac-toe driven by the shared GameSession.

Same UX as before — prompts for mode, accepts ``A1``..``C3`` cells, ``reset``
and ``quit``. All game state and hardware motion lives in
``game_session.GameSession`` so the web app (``web/app.py``) shares the exact
same code path.

Run::

    python protocols/tic_tac_toe.py
"""

import sys
from pathlib import Path

# Make the demo root importable when run as a script (so `game_session`,
# `game_logic`, `app_runtime`, and `tools/` resolve from anywhere).
DEMO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DEMO_ROOT))

from app_runtime import build_session, load_configs, shutdown  # noqa: E402
from game_logic import display_board  # noqa: E402

# ── UI ────────────────────────────────────────────────────────────────


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


def _print_outcome(session):
    if session.status.endswith("Wins"):
        winner = session.status.replace("Wins", "")
        if session.mode == 1:
            print("You win!" if winner == session.human_symbol else "AI wins!")
        else:
            print(f"Player {'1' if winner == 'X' else '2'} ({winner}) wins!")
    elif session.status == "Draw":
        print("Draw!")


def _confirm_quit(session):
    """Ask whether to reset before quitting. Returns False (quit signal)."""
    if session.move_history:
        while True:
            choice = input("Reset board before quitting? (y/n): ").strip().lower()
            if choice in ("y", "yes"):
                session.reset()
                break
            if choice in ("n", "no"):
                print("Board left as-is.")
                break
            print("Invalid.")
    return False


def play_game(session):
    """Run one CLI game against ``session``. Returns True to play again."""
    num_players, human_symbol, ai_difficulty = select_mode()
    session.start(
        mode=num_players,
        human_symbol=human_symbol,
        ai_difficulty=ai_difficulty,
    )

    if num_players == 1:
        print(f"\nYou: {human_symbol}  |  AI: {session.ai_symbol} ({ai_difficulty})")
    else:
        print("\nPlayer 1: X  |  Player 2: O")
    print("Moves: A1-C3 | 'reset' | 'quit'\n")

    while session.status == "InProgress":
        display_board(session.board)

        if num_players == 1:
            prompt = f"Your move ({session.human_symbol}): "
        else:
            prompt = f"Player {'1' if session.current == 'X' else '2'} ({session.current}): "

        text = input(prompt).strip()
        if text.lower() == "quit":
            return _confirm_quit(session)
        if text.lower() == "reset":
            session.reset()
            return True

        try:
            session.make_move(text)
        except (ValueError, RuntimeError) as e:
            print(f"  {e}")
            continue

    display_board(session.board)
    _print_outcome(session)

    while True:
        choice = input("\n(p)lay again / (q)uit: ").strip().lower()
        if choice in ("p", "play"):
            session.reset()
            return True
        if choice in ("q", "quit"):
            return _confirm_quit(session)
        print("Invalid.")


def main():
    cnc_cfg, _ = load_configs()
    virtual = cnc_cfg.get("virtual", False)
    move_speed = cnc_cfg.get("move_speed", 2500)

    session, cnc, gripper = build_session()
    try:
        playing = True
        while playing:
            playing = play_game(session)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        shutdown(cnc, gripper, virtual=virtual, move_speed=move_speed)


main()
