"""Shared tic-tac-toe game state for both the CLI protocol and the web app.

The ``GameSession`` owns the per-game state that previously lived in the CLI
loop locals (``board``, ``state``, ``move_history``, ``current``,
``mode``/``human_symbol``/``ai_difficulty``) plus the hardware handles
(``cnc``, ``gripper``, ``deck``). Methods are thread-safe via a single
``threading.Lock`` so concurrent HTTP requests cannot drive the gantry into
itself.

Public API (everything else is internal):

    session = GameSession(cnc, gripper, deck, virtual=...)
    session.start(mode=1|2, human_symbol="X"|"O", ai_difficulty="easy"|...)
    session.make_move("A1")               # human move; auto-plays AI if needed
    session.reset()                       # returns every piece to storage
    session.snapshot()                    # dict for UI rendering
"""

from __future__ import annotations

import threading
from pathlib import Path

import yaml

from cnc_machine_core import DeckState

from game_logic import (
    AI_LEVELS,
    BOARD_WELL_MAP,
    STORAGE_WELLS,
    board_label,
    check_winner,
    is_draw,
    new_board,
    parse_input,
)


class GameSession:
    """In-memory game state shared between CLI and web frontends."""

    def __init__(
        self,
        cnc,
        gripper,
        deck,
        *,
        slot_storage: str,
        slot_board: str,
        z_pick: float,
        z_place: float,
        move_speed: int,
        preset_path: Path,
        state_output: Path | None,
        virtual: bool,
        travel: dict | None = None,
    ):
        self.cnc = cnc
        self.gripper = gripper
        self.deck = deck
        self.slot_storage = slot_storage
        self.slot_board = slot_board
        self.z_pick = z_pick
        self.z_place = z_place
        self.move_speed = move_speed
        self.preset_path = preset_path
        self.state_output = state_output
        self.virtual = virtual
        self.offset = gripper.offset
        self.travel = travel  # {"axis_order": ..., "x_offset": ..., "y_waypoint": ...} or None
        self._last_xy: tuple[float, float] | None = None  # for relative routing
        self._pending_ai: tuple[int, int] | None = None  # cached AI decision

        self._lock = threading.Lock()

        # Per-game state — populated by start()
        self.state: DeckState | None = None
        self.board: list[list[str | None]] | None = None
        self.move_history: list[tuple[str, str, str]] = []
        self.current: str = "O"
        self.mode: int | None = None
        self.human_symbol: str | None = None
        self.ai_symbol: str | None = None
        self.ai_difficulty: str | None = None
        self.status: str = "Idle"  # Idle | InProgress | XWins | OWins | Draw

    # ── Hardware primitives ────────────────────────────────────────────

    def _xy(self, slot, well):
        x, y, _ = self.deck.get_labware(slot)[well].position(offset=self.offset)
        return x, y

    def _travel_to(self, x, y, z):
        """Route to (x, y, z). Orthogonal dogleg if configured AND source is known."""
        if self.travel and self._last_xy is not None:
            order = self.travel.get("axis_order", "yxy")
            src_x, src_y = self._last_xy
            if order == "yxy":
                wp = src_y + float(self.travel.get("y_offset", 0.0))
            elif order == "xyx":
                wp = src_x + float(self.travel.get("x_offset", 0.0))
            elif order == "xyxy":
                wp = [
                    src_x + float(self.travel.get("x_offset", 0.0)),
                    float(self.travel["y_waypoint"]),
                ]
            elif order == "yxyx":
                wp = [
                    src_y + float(self.travel.get("y_offset", 0.0)),
                    float(x) + float(self.travel.get("x_approach", 0.0)),
                ]
            else:
                wp = None
            if wp is not None:
                self.cnc.move_to_point_safe_orthogonal(
                    x, y, z,
                    waypoint=wp,
                    axis_order=order,
                    speed=self.move_speed,
                )
            else:
                self.cnc.move_to_point_safe(x, y, z, speed=self.move_speed)
        else:
            self.cnc.move_to_point_safe(x, y, z, speed=self.move_speed)
        self._last_xy = (x, y)

    def _pick_and_place(self, storage_well, board_well):
        sx, sy = self._xy(self.slot_storage, storage_well)
        bx, by = self._xy(self.slot_board, board_well)
        self._travel_to(sx, sy, self.z_pick)
        self.gripper.engage()
        self._travel_to(bx, by, self.z_place)
        self.gripper.release()

    def _return_piece(self, board_well, storage_well):
        bx, by = self._xy(self.slot_board, board_well)
        sx, sy = self._xy(self.slot_storage, storage_well)
        self._travel_to(bx, by, self.z_pick)
        self.gripper.engage()
        self._travel_to(sx, sy, self.z_place)
        self.gripper.release()

    # ── State helpers ──────────────────────────────────────────────────

    def _load_preset(self):
        with open(self.preset_path, "r", encoding="utf-8") as f:
            preset = yaml.safe_load(f)
        state_file = str(self.state_output) if self.state_output else None
        state = DeckState(state_file=state_file)
        state.init_from_preset(preset)
        return state

    def _next_storage_well(self, piece):
        for well in STORAGE_WELLS[piece]:
            if self.state.get_status(self.slot_storage, well) == f"{piece}_piece":
                return well
        return None

    def _recompute_status(self):
        winner = check_winner(self.board)
        if winner:
            self.status = f"{winner}Wins"
        elif is_draw(self.board):
            self.status = "Draw"
        else:
            self.status = "InProgress"

    def _play_one(self, row, col, *, log_prefix=""):
        """Execute a single move for ``self.current`` at (row, col). Caller holds lock."""
        storage_well = self._next_storage_well(self.current)
        if storage_well is None:
            raise RuntimeError(f"No {self.current} pieces left in storage")
        board_well = BOARD_WELL_MAP[(row, col)]

        if self.virtual:
            print(
                f"  {log_prefix}[VIRTUAL] {self.current}: storage {storage_well} -> board {board_well}"
            )
        else:
            self._pick_and_place(storage_well, board_well)

        self.board[row][col] = self.current
        self.state.set_status(self.slot_storage, storage_well, "empty")
        self.state.set_status(self.slot_board, board_well, self.current)
        self.move_history.append((self.current, storage_well, board_well))
        self.current = "O" if self.current == "X" else "X"
        self._recompute_status()

    # ── Public API ─────────────────────────────────────────────────────

    def start(self, mode: int, human_symbol: str | None = None, ai_difficulty: str | None = None, *, auto_play_ai: bool = True):
        """Begin a new game. Resets the in-memory board (does NOT move hardware).

        ``auto_play_ai=False`` (web UI) lets the caller decide when to trigger
        the AI's turn so the cell can be highlighted first.
        """
        if mode not in (1, 2):
            raise ValueError(f"mode must be 1 or 2, got {mode!r}")
        if mode == 1:
            if human_symbol not in ("X", "O"):
                raise ValueError("human_symbol must be 'X' or 'O' for 1-player mode")
            if ai_difficulty not in AI_LEVELS:
                raise ValueError(f"ai_difficulty must be one of {list(AI_LEVELS)}")

        with self._lock:
            self.state = self._load_preset()
            self.board = new_board()
            self.move_history = []
            self.current = "O"  # O always opens
            self.mode = mode
            self.human_symbol = human_symbol
            self.ai_symbol = (
                ("O" if human_symbol == "X" else "X") if mode == 1 else None
            )
            self.ai_difficulty = ai_difficulty if mode == 1 else None
            self.status = "InProgress"
            self._pending_ai = None

            # If AI opens (human chose X, O goes first), let it play immediately
            # — but only in CLI mode. Web sets auto_play_ai=False.
            if auto_play_ai and self.mode == 1 and self.current == self.ai_symbol:
                self._play_ai_turn_if_needed()

        return self.snapshot()

    def make_move(self, cell: str, *, auto_play_ai: bool = True):
        """Apply a human move (``"A1"``..``"C3"``). Auto-plays AI unless disabled."""
        pos = parse_input(cell)
        if pos is None:
            raise ValueError(f"Invalid cell {cell!r} (use A1..C3)")
        row, col = pos

        with self._lock:
            if self.status != "InProgress":
                raise RuntimeError(f"Game is not in progress (status={self.status})")
            if self.board[row][col] is not None:
                raise RuntimeError(f"Cell {cell} is already occupied")
            if self.mode == 1 and self.current != self.human_symbol:
                raise RuntimeError("Not your turn — AI is about to play")

            self._play_one(row, col)
            if auto_play_ai:
                self._play_ai_turn_if_needed()

        return self.snapshot()

    def peek_ai_move(self) -> str | None:
        """Return AI's next move as ``"A1"`` (decided + cached). None if not AI's turn."""
        with self._lock:
            rc = self._ensure_ai_decision()
            return board_label(*rc) if rc else None

    def play_ai_move(self):
        """Execute the (possibly cached) AI move and return the new snapshot."""
        with self._lock:
            self._play_ai_turn_if_needed()
        return self.snapshot()

    def _ensure_ai_decision(self):
        """Decide AI's next move if needed and cache it. Caller holds lock."""
        if (
            self.mode == 1
            and self.status == "InProgress"
            and self.current == self.ai_symbol
            and self._pending_ai is None
        ):
            ai_fn = AI_LEVELS[self.ai_difficulty]
            self._pending_ai = ai_fn(self.board, self.current)
        return self._pending_ai

    def _play_ai_turn_if_needed(self):
        """Run the AI move if it's the AI's turn and the game is still live. Caller holds lock."""
        rc = self._ensure_ai_decision()
        if rc is None:
            return
        row, col = rc
        self._pending_ai = None
        print(f"  AI ({self.current}) plays: {board_label(row, col)}")
        self._play_one(row, col, log_prefix="AI ")

    def reset(self):
        """Return every placed piece to its storage well, in reverse order."""
        with self._lock:
            if self.state is None or self.board is None:
                return self.snapshot()
            if self.move_history:
                print("\nResetting board...")
                for piece, storage_well, board_well in reversed(self.move_history):
                    print(f"  {piece}: board {board_well} -> storage {storage_well}")
                    if not self.virtual:
                        self._return_piece(board_well, storage_well)
                    self.state.set_status(self.slot_board, board_well, "empty")
                    self.state.set_status(
                        self.slot_storage, storage_well, f"{piece}_piece"
                    )
            self.board = new_board()
            self.move_history = []
            self.current = "O"
            self.status = "Idle"
            self.mode = None
            self.human_symbol = None
            self.ai_symbol = None
            self.ai_difficulty = None
            self._pending_ai = None

        return self.snapshot()

    def snapshot(self):
        """Return a JSON-serialisable view of the current state."""
        is_ai_turn = (
            self.status == "InProgress"
            and self.mode == 1
            and self.current == self.ai_symbol
        )
        return {
            "board": [list(row) for row in (self.board or new_board())],
            "current_player": self.current,
            "game_status": self.status,
            "game_mode": self.mode,
            "human_symbol": self.human_symbol,
            "ai_symbol": self.ai_symbol,
            "ai_difficulty": self.ai_difficulty,
            "move_history": [
                f"{p}: storage {s} -> board {b}" for p, s, b in self.move_history
            ],
            "is_ai_turn": is_ai_turn,
        }
