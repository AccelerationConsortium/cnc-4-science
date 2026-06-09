# Serial Dilution Demo

A 1:2 serial dilution across a 24-well plate, run on a Genmitsu CNC machine with a Sartorius Picus 2 5000µL electronic pipette.

This is a worked example of how to build an application on top of [`cnc-4-science`](https://github.com/AccelerationConsortium/cnc-4-science). Copy this directory to start your own protocol.

## Deck layout

| Slot | Position    | Labware                              | Role                                    |
| ---- | ----------- | ------------------------------------ | --------------------------------------- |
| 1    | front-left  | `corning_24_wellplate_3.4ml_flat`    | dilution target                         |
| 2    | front-right | `sartorius_24_tiprack_5000ul`        | 5000µL tip rack                         |
| 3    | back-left   | `opentrons_tough_4_reservoir_72ml`   | A1 = stock, A2 = diluent                |
| 4    | back-right  | `sartorius_24_tiprack_5000ul`        | tip waste                               |

## Workflow

1. **Phase 1 — Prefill.** Pick up a tip, prefill 23 wells (`B1..D6`) with 1750µL diluent from reservoir A2, discard tip.
2. **Phase 2 — Dilute.** Pick up a new tip, transfer 3500µL stock from reservoir A1 into plate A1, then serial-dilute 1:2 column-by-column (`A1→B1→C1→D1→A2→…→D6`) with 3 mixes per step. Discard tip.

## Hardware

- Genmitsu CNC machine with GRBL firmware (tested on 4040-PRO)
- Sartorius Picus 2 electronic pipette (USB serial, 230400 baud)
- 24-well Corning plate, Opentrons 4-reservoir tough plate, Sartorius 5000µL tips

## Setup

```powershell
# Windows
cd templates\serial_dilution_demo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux / macOS
cd templates/serial_dilution_demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

Open [protocol.py](protocol.py) and edit the constants at the top:

```python
COM_PORT_CNC = "COM4"          # serial port for the CNC controller
COM_PORT_PIPETTE = "COM3"      # serial port for the Picus 2 pipette
VIRTUAL = False                # True = dry-run (no hardware needed)
```

Calibrated Z heights are also at the top of the file — they assume a freshly homed machine with the pipette tool installed. Recalibrate with `z_helper.py` if your geometry differs.

## Calibrate Z heights

```bash
python z_helper.py
```

Interactive: prompts for tool, slot, well, then lets you jog Z up/down at coarse/medium/fine steps until the tip is at the correct height. Press `s` to save the value (written to `output/z_calibration.yaml`). Use the saved value to update `Z_PLATE_ASPIRATE`, `Z_PLATE_DISPENSE`, `Z_RESERVOIR`, `Z_TIP_PICKUP` in `protocol.py`.

## Run

```bash
python protocol.py
```

The protocol prints each move it makes and writes the final deck state to `output/deck_state.yaml`.

To dry-run without hardware, set `VIRTUAL = True` at the top of `protocol.py`.

## Directory layout

```
serial_dilution_demo/
├── README.md
├── requirements.txt
├── protocol.py                  # main protocol — `python protocol.py`
├── z_helper.py                  # Z calibration helper — `python z_helper.py`
├── tool_definitions.json        # pipette offset, COM port, default speed
├── deck_preset.yaml             # initial deck state (well statuses)
├── custom_labware/
│   └── sartorius_24_tiprack_5000ul.json
├── tools/
│   ├── sartorius_pipette.py     # thin wrapper around the picus driver
│   └── picus/                   # vendored Sartorius Picus 2 driver
└── output/                      # state files written here at runtime
```

## Customising

- **Change well count / volume:** edit `PREFILL_VOLUME`, `STOCK_VOLUME`, `DILUTION_VOLUME`, `MIX_VOLUME`, `MIX_CYCLES` in `protocol.py`.
- **Change labware:** swap the `load_definition(...)` calls in `protocol.py` (and matching slots in `z_helper.py` + `deck_preset.yaml`). Browse standard labware at [labware.opentrons.com](https://labware.opentrons.com/).
- **Add a different tool:** add a new entry to `tool_definitions.json` and a wrapper class under `tools/` following the pattern in `sartorius_pipette.py`.
