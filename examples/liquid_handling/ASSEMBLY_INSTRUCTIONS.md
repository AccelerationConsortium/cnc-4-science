# Assembly instructions — liquid handling (Sartorius Picus)

Full hardware build for the Picus-pipette serial-dilution example.

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

### Per-tool (Picus pipette)

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Sartorius Picus electronic pipette | _Sartorius_ | _$$$_ | Verified with the 5000 µL head. |
| 1   | Picus USB cable | _Sartorius_ | _$\<n\>_ | Serial control from the host PC. |
| 1   | 3D-printed pipette holster | _self-print, see CAD below_ | _$\<material\>_ | Clamps the Picus body to the spindle carriage. |
| _N_ | Picus-compatible tips | _Sartorius_ | _$\<n\>/box_ | Volume matches your protocol. |
| _N_ | Standard SBS labware (source / dest plates) | _\<vendor\>_ | _$\<n\>_ | Sourced from `opentrons-shared-data` definitions; see [`deck_preset.yaml`](deck_preset.yaml). |

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

### Stage 3 — Picus pipette

1. Print the Picus holster and bolt it to the spindle carriage in place of the
   stock spindle.
2. Slide the Picus into the holster and tighten the clamp; the tip should hang
   below the gantry by enough to reach the deepest labware well plus a few mm
   clearance.
3. Plug the Picus USB cable into the host PC. Confirm the port name and set it
   in [`tools/picus_config.yaml`](tools/picus_config.yaml).
4. Run `python z_helper.py` from this directory to calibrate aspirate /
   dispense / tip-pickup / tip-eject Z heights, then copy them into
   [`tools/cnc_config.yaml`](tools/cnc_config.yaml) under `z_heights:`.

---

## CAD

| File | Description | Print settings | Notes |
| ---- | ----------- | -------------- | ----- |
| _TBD_ | 4-slot SBS deck plate | 0.2 mm layer, 30% infill, PETG (or 6 mm aluminum) | Same plate every example uses. |
| _TBD_ | Picus pipette holster | 0.2 mm layer, 30% infill, PETG | Mounts to spindle carriage. Match clamp geometry to your Picus model. |

## Safety

_TODO: emergency-stop location, what to do if the pipette crashes into the
deck, when to power-cycle vs re-home, GRBL alarm states._
