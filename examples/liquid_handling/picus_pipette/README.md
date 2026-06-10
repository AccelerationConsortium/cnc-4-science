# Liquid Handling — Serial Dilution (Sartorius Picus 2)

1:2 serial dilution across a 24-well plate using a Sartorius **Picus 2** 5000 µL pipette on a Genmitsu CNC machine.

This folder doubles as a **template** for building your own CNC-based protocols — copy it, swap the tool, edit the configs.

- **Phase 1 — Prefill.** Pick up a tip, prefill 23 wells (`B1..D6`) with diluent from reservoir A2 (batched aspirations), discard tip.
- **Phase 2 — Dilute.** Pick up a new tip, transfer stock from reservoir A1 into plate A1, then serial-dilute column-by-column (`A1→B1→…→D6`) with a mix per step.

Default volumes (1100 µL prefill / 2200 µL transfer) give a 2:1 mixing ratio per step (each well ≈ 67% of previous).

## Deck layout

| Slot | Position    | Role        | Labware                              |
| ---- | ----------- | ----------- | ------------------------------------ |
| 1    | front-left  | `plate`     | `corning_24_wellplate_3.4ml_flat`    |
| 2    | front-right | `tips`      | `sartorius_24_tiprack_5000ul`        |
| 3    | back-left   | `reservoir` | `opentrons_tough_4_reservoir_72ml` (A1 = stock, A2 = diluent) |
| 4    | back-right  | `waste`     | `sartorius_24_tiprack_5000ul`        |

Slot assignment lives in [tools/cnc_config.yaml](tools/cnc_config.yaml) under `deck:` — change it there, not in the protocol.

## Run

```bash
pip install -r requirements.txt

# Edit COM ports to match your setup:
#   tools/cnc_config.yaml    (CNC port, bounds, Z heights, deck layout)
#   tools/picus_config.yaml  (pipette port, offset, volumes)

# Optional: set virtual: true in tools/cnc_config.yaml to dry-run without hardware.
python protocols/serial_dilution_demo.py
```

Final deck state is written to `output/deck_state.yaml`.

## Calibrate Z heights

```bash
python z_helper.py
```

Interactive: jogs Z at coarse/medium/fine steps, saves to `output/z_calibration.yaml`. Copy values into the `z_heights:` block of `tools/cnc_config.yaml`.

## Directory layout

```
picus_pipette/
├── README.md
├── requirements.txt
├── z_helper.py                     # Z calibration helper (interactive)
├── protocols/
│   └── serial_dilution_demo.py     # the protocol (main entry point)
├── tools/
│   ├── cnc_config.yaml             # CNC + deck layout + Z heights
│   ├── picus_config.yaml           # Picus pipette: port, offset, volumes
│   ├── picus_pipette.py            # PicusPipette wrapper (used by protocols)
│   └── picus_driver.py             # vendored low-level Picus 2 driver
├── deck_preset.yaml                # initial deck state (well statuses)
├── custom_labware/
│   └── sartorius_24_tiprack_5000ul.json
└── output/                         # state files written here at runtime
```

## Using this as a template

To adapt for a different tool or protocol:

1. **Copy this folder.** Rename `picus_pipette/` to match your tool, e.g. `peristaltic_pump/`.
2. **Replace the driver.** Drop your vendor driver into `tools/` (e.g. `pump_driver.py`) and write a thin wrapper (`tools/pump.py`) exposing the methods your protocol needs.
3. **Add a tool config.** Create `tools/<tool>_config.yaml` with the tool's serial port, mounting offset, and any tool-specific parameters.
4. **Edit `cnc_config.yaml`.** Update `deck:` slot roles + labware comments to match your deck. Calibrate Z heights with `z_helper.py`.
5. **Write your protocol** in `protocols/`. Load the two configs at the top and use the tool wrapper. The dilution demo is a worked reference.
