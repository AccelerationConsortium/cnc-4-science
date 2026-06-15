# Vacuum Pick-and-Place — Physical Tic-Tac-Toe (CLI)

Plays tic-tac-toe on a real 3×3 board using a CNC gantry and a vacuum gripper.
Pieces are picked from a storage rack (X and O reservoirs) and placed on the
game board, one move at a time. The same gripper returns every piece to
storage at end-of-game.

Two-player or 1-player vs AI (Easy / Medium / Hard).

This example doubles as a **template for any vacuum-driven pick-and-place
workflow** — the gripper is just a thin wrapper around the CNC's spindle
output (M3/M5), so swapping in any electromagnet, gripper, or solenoid that
the controller can switch is a one-file change.

---

## 1. Hardware setup (~1 hour)

See [ASSEMBLY_INSTRUCTIONS.md](ASSEMBLY_INSTRUCTIONS.md) for the full BOM,
print list, wiring, and step-by-step build. Come back here when the gantry is
mounted, the deck is squared, the vacuum gripper is wired, and the pump turns
on when GRBL sends `M3`.

## 2. Software setup

```bash
# 1. Create + activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows
# source .venv/bin/activate      # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt
```

Edit the two config files in [`tools/`](tools/):

- [`tools/cnc_config.yaml`](tools/cnc_config.yaml) — CNC COM port, travel bounds, Z heights, deck layout.
- [`tools/vacuum_config.yaml`](tools/vacuum_config.yaml) — vacuum RPM, settle delays, XY offset.

> Set `virtual: true` in `cnc_config.yaml` to dry-run the protocol without
> any hardware connected.

> The shipped `z_heights:` (`pick: -21.0`, `place: -19.0`) are calibrated for
> the reference build in [ASSEMBLY_INSTRUCTIONS.md](ASSEMBLY_INSTRUCTIONS.md).
> If your build differs, remeasure by hand — jog Z until the suction cup just
> kisses the top of a storage piece (→ `pick`) and just above a board cell
> rim (→ `place`), then edit `z_heights:`. See
> [docs/SETUP.md §4](../../docs/SETUP.md#4-calibrate-z-heights).

## 3. Run

```bash
python protocols/tic_tac_toe.py
```

The CLI prompts for game mode and accepts cell labels `A1`..`C3`. Commands
during play:

| Input        | Effect                                      |
| ------------ | ------------------------------------------- |
| `A1`..`C3`   | Place at that cell                          |
| `reset`      | Return every placed piece to storage        |
| `quit`       | Exit; optionally reset board first          |

Deck state is auto-saved to `output/deck_state.yaml` after every move, so
a crashed game resumes from the last known state.

### Optional: browser UI

A lightweight FastAPI frontend drives the same `GameSession` as the CLI (same
lock, same hardware handles, same state) — you cannot accidentally drive the
gantry from both at once.

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Then open <http://localhost:8000/>. 3×3 clickable board with mode / difficulty
/ symbol selectors, reset button, AI peek-and-play handshake (board flashes
the next CNC move before the gantry executes), and a collapsed debug bar with
the API request log. `virtual: true` works exactly the same way — the browser
drives the full game loop, just without any actual motion.

---

## Reference

### Deck layout

| Slot | Position    | Role       | Labware                              |
| ---- | ----------- | ---------- | ------------------------------------ |
| 1    | front-left  | `storage`  | `storage_15_tuberack_100ul`          |
| 2    | front-right | `gameboard`| `gameboard_15_tuberack_100ul`        |
| 3    | back-left   | *(empty)*  |                                      |
| 4    | back-right  | *(empty)*  |                                      |

Storage rack (slot 1): O pieces in columns 1-2, X pieces in columns 4-5
(see `STORAGE_WELLS` in [game_logic.py](game_logic.py)).

Game board (slot 2): 3×3 play area occupies columns 2-4 of the 15-well rack
(see `BOARD_WELL_MAP` in [game_logic.py](game_logic.py)).

Slot assignment lives in [tools/cnc_config.yaml](tools/cnc_config.yaml) under
`deck:` — change it there, not in the protocol.

### What's different from the liquid handling demo

| Aspect            | Liquid handling                        | This example                                |
| ----------------- | -------------------------------------- | ------------------------------------------- |
| Tool              | Sartorius Picus 2 pipette              | Vacuum gripper (suction cup on spindle)     |
| Tool comms        | Separate serial port (`COM3`)          | **None** — uses CNC's spindle output        |
| Tool wrapper      | [`PicusPipette`](../liquid_handling/tools/picus_pipette.py) calls vendor driver | [`VacuumGripper`](tools/vacuum_gripper.py) calls `cnc.spindle_on()` / `cnc.spindle_off()` |
| Tool config       | port, baud, volumes                    | RPM, settle delays (no port)                |
| Labware           | Opentrons standard + custom tiprack    | Two custom 15-well racks (storage + board)  |
| Workflow          | Linear (prefill → dilute)              | **Interactive** — CLI prompts for moves     |

### Directory layout

```
vacuum_pick_and_place/
├── README.md
├── ASSEMBLY_INSTRUCTIONS.md
├── requirements.txt
├── game_logic.py                       # board + AI (pure Python, no CNC)
├── game_session.py                     # shared state machine (CLI + web)
├── app_runtime.py                      # config loading + CNC/gripper bootstrap
├── protocols/
│   └── tic_tac_toe.py                  # CLI entry point (thin loop over GameSession)
├── web/
│   ├── app.py                          # FastAPI: /api/state | /start | /move | /ai-move | /reset
│   └── static/
│       ├── index.html
│       ├── game.js
│       └── style.css
├── tools/
│   ├── cnc_config.yaml                 # CNC + deck layout + Z heights
│   ├── vacuum_config.yaml              # vacuum: RPM, delays, offset
│   └── vacuum_gripper.py               # VacuumGripper wrapper (uses CNC spindle)
├── presets/
│   └── ttt_preset.yaml                 # initial deck state (X/O storage, empty board)
├── custom_labware/
│   ├── storage_15_tuberack_100ul.json
│   └── gameboard_15_tuberack_100ul.json
└── output/                             # state files written here at runtime
```

### Using this as a template

To adapt for a different vacuum/spindle-switched tool:

1. **Copy this folder** to a new directory.
2. **Edit `tools/vacuum_gripper.py`** if your "tool" semantics differ (e.g.
   electromagnet → rename methods to `magnet_on` / `magnet_off`, keep the
   `cnc.spindle_on/off` underneath).
3. **Add a tool config.** Update `tools/vacuum_config.yaml` with the on-value
   (RPM / PWM duty), any settle delays, and the XY/Z mount offset.
4. **Edit `cnc_config.yaml`.** Update `deck:` slot roles + labware comments
   to match your deck. Measure Z heights by hand (jog with a GRBL UI like
   [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations)
   or `cnc.move_to_point(...)` from a Python shell) and write them into
   `z_heights:` — see [docs/SETUP.md §4](../../docs/SETUP.md#4-calibrate-z-heights).
5. **Write your protocol** in `protocols/`. The `_pick_and_place()` helper in
   [game_session.py](game_session.py) is a one-screen reference. If you also
   want a web UI, copy [web/app.py](web/app.py) — the FastAPI layer is
   ~100 lines and reuses whatever `GameSession`-style state machine you build.
