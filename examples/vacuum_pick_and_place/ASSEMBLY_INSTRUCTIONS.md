# Assembly instructions — vacuum pick-and-place

Full hardware build for the vacuum pick-and-place tic-tac-toe example.

**Target time:** ~1 hour, once all parts are in hand and 3D-printed.

When you're done here, jump back to the [README](README.md) for the software
setup (venv → `pip install` → configure YAML → smoke test → run).

---

## BOM

### Base CNC + deck

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Genmitsu 3018-PROVer / equivalent GRBL CNC | _e.g. SainSmart_ | _$300_ | Travel ~300x180x45 mm. Verify your bounds in [`tools/cnc_config.yaml`](tools/cnc_config.yaml). |
| 1   | 24 V power supply | _included with most kits_ | _included_ | |
| 1   | USB-A to USB-B cable | _generic_ | _$5_ | To the host PC. |
| _TBD_ | Deck plate (3D-printed or aluminum) | _self-print_ | _$\<material\>_ | Footprint matches [`cnc_4_slot_deck.json`](../../src/cnc_machine_core/deck/cnc_4_slot_deck.json). |
| _TBD_ | SBS labware spacers / clips | _\<vendor\>_ | _$\<n\>_ | Hold labware square in each slot. |

### Per-tool (vacuum gripper)

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Vacuum pump (12 V) | _\<vendor\>_ | _$\<n\>_ | Wired directly to the GRBL spindle terminals (M3 / M5 toggles the pump). |
| 1   | Suction cup, ~5 mm OD | _\<vendor\>_ | _$\<n\>_ | Sized to the tic-tac-toe pieces (or whatever you're picking). |
| 1   | Silicone tubing, 4 mm ID | _\<vendor\>_ | _$\<n\>_ | From pump → gripper. |
| 1   | 3D-printed gripper mount | _self-print, see CAD below_ | _$\<material\>_ | Bolts onto the spindle carriage. |
| 15  | Tic-tac-toe pieces (X / O) | _self-print or wood_ | _$\<n\>_ | Fit the 100 µL custom labware wells. |

---

## Assembly

### Stage 1 — Base CNC

1. Unbox the gantry and mount it on a stable surface.
2. Confirm GRBL is preloaded (most Genmitsu kits ship preloaded). Flash it if
   not.
3. Confirm homing works in [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations)
   or another GRBL UI before the Python library ever touches it.

_TODO: photos, wiring, limit-switch check, work-zero procedure._

### Stage 2 — Deck

1. Install the deck plate onto the CNC bed.
2. Square it against the X / Y axes and fix it down. Once squared, slot
   positions are fixed forever and should not need re-tuning.

_TODO: bolt pattern, photo of the mounted deck with slot 1 labeled, MPos
verification procedure._

### Stage 3 — Vacuum gripper

1. Print the gripper mount and bolt it to the spindle carriage in place of the
   stock spindle. The suction cup should sit at roughly the same Z as the
   spindle bit it replaces.
2. Glue the suction cup to the bottom of the gripper mount.
3. Cut a length of silicone tubing from the pump outlet to the gripper inlet.
4. Wire the vacuum pump to the GRBL spindle terminals on the controller board.
   Verify polarity — the pump should turn on when GRBL sends `M3` and off on
   `M5`.
5. Run `python z_helper.py` from this directory to calibrate the pick / place
   Z heights, then copy them into [`tools/cnc_config.yaml`](tools/cnc_config.yaml)
   under `z_heights:`.

---

## CAD

| File | Description | Print settings | Notes |
| ---- | ----------- | -------------- | ----- |
| _TBD_ | 4-slot SBS deck plate | 0.2 mm layer, 30% infill, PETG (or 6 mm aluminum) | Same plate every example uses. |
| _TBD_ | Vacuum gripper mount | 0.2 mm layer, 30% infill, PETG | Mounts to spindle carriage. |
| [`custom_labware/storage_15_tuberack_100ul.json`](custom_labware/storage_15_tuberack_100ul.json) + (CAD TBD) | Storage rack (15 pieces, 5x3) | _\<material\>_ | Holds unplaced X/O pieces. |
| [`custom_labware/gameboard_15_tuberack_100ul.json`](custom_labware/gameboard_15_tuberack_100ul.json) + (CAD TBD) | Game board (3x3 play area, ignore outer wells) | _\<material\>_ | The actual tic-tac-toe board. |

## Safety

_TODO: emergency-stop location, what to do if the gripper crashes into the
deck, when to power-cycle vs re-home, GRBL alarm states._
