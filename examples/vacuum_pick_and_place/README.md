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

## What's different from the liquid handling demo

| Aspect            | Liquid handling                        | This example                                |
| ----------------- | -------------------------------------- | ------------------------------------------- |
| Tool              | Sartorius Picus 2 pipette              | Vacuum gripper (suction cup on spindle)     |
| Tool comms        | Separate serial port (`COM3`)          | **None** — uses CNC's spindle output        |
| Tool wrapper      | [`PicusPipette`](../liquid_handling/tools/picus_pipette.py) calls vendor driver | [`VacuumGripper`](tools/vacuum_gripper.py) calls `cnc.spindle_on()` / `cnc.spindle_off()` |
| Tool config       | port, baud, volumes                    | RPM, settle delays (no port)                |
| Labware           | Opentrons standard + custom tiprack    | Two custom 15-well racks (storage + board)  |
| Workflow          | Linear (prefill → dilute)              | **Interactive** — CLI prompts for moves     |

## Deck layout

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

## Run

```bash
pip install -r requirements.txt

# Edit ports / bounds to match your setup:
#   tools/cnc_config.yaml     (CNC port, bounds, Z heights, deck layout)
#   tools/vacuum_config.yaml  (vacuum RPM, settle delays, offset)

# Optional: set virtual: true in tools/cnc_config.yaml to dry-run without hardware.
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

## Calibrate Z heights

The shipped values (`pick: -21.0`, `place: -19.0`) are calibrated for one
specific setup and almost certainly wrong for yours. Re-run the helper:

```bash
python ../liquid_handling/z_helper.py
```

It is generic across examples — point it at your labware and tool, jog Z to
where the vacuum cup just kisses the top of a piece (for `pick`) and just
above the board cell rim (for `place`), and copy the values into the
`z_heights:` block of `tools/cnc_config.yaml`.

> **Note on the tool wrapper.** Because the vacuum doesn't have a serial
> port, `z_helper.py` will only see the `offset:` from
> `tools/vacuum_config.yaml` for XY centering. You still need to think about
> Z separately per action — see [docs/SETUP.md §4](../../docs/SETUP.md#4-calibrate-z-heights).

## Directory layout

```
vacuum_pick_and_place/
├── README.md
├── requirements.txt
├── game_logic.py                       # board + AI (pure Python, no CNC)
├── protocols/
│   └── tic_tac_toe.py                  # the CLI protocol (main entry point)
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

## Using this as a template

To adapt for a different vacuum/spindle-switched tool:

1. **Copy this folder** to a new directory.
2. **Edit `tools/vacuum_gripper.py`** if your "tool" semantics differ (e.g.
   electromagnet → rename methods to `magnet_on` / `magnet_off`, keep the
   `cnc.spindle_on/off` underneath).
3. **Add a tool config.** Update `tools/vacuum_config.yaml` with the on-value
   (RPM / PWM duty), any settle delays, and the XY/Z mount offset.
4. **Edit `cnc_config.yaml`.** Update `deck:` slot roles + labware comments
   to match your deck. Recalibrate Z with `z_helper.py`.
5. **Write your protocol** in `protocols/`. The `pick_and_place()` helper in
   [tic_tac_toe.py](protocols/tic_tac_toe.py) is a one-screen reference.
