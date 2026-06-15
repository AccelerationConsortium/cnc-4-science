# Assembly instructions — vacuum pick-and-place

Full hardware build for the vacuum-gripper tic-tac-toe example. The vacuum
pump is wired into the CNC's spindle terminals, so GRBL's `M3` / `M5` toggles
the suction — no separate microcontroller or USB cable is needed for the
gripper.

**Target time:** ~1 hour, once parts are in hand and 3D-printed.

Source of truth for this BOM is [bom.csv](bom.csv) (sheet
`pick_and_place_cnc_demo` of [`docs/bom.xlsx`](../../docs/bom.xlsx)).

When you're done here, jump back to the [README](README.md) for the software
setup (venv → `pip install` → configure YAML → smoke test → run).

---

## Purchased parts

| # | Part | Qty | ~Cost (USD) | Link | Notes |
| - | ---- | --: | ----------: | ---- | ----- |
| A1 | Genmitsu 3018-PROVer V2 CNC | 1 | 256 | [Amazon](https://www.amazon.ca/Genmitsu-3018-PROVer-Beginner-Emergency-Stop-Spoilboard/dp/B0CMTJ6CZC) | Follow the [SainSmart assembly manual](https://docs.sainsmart.com/article/appuv0ufmb-3018-prover-v-2) up to section 3, skipping steps 2.4 / 2.5 (spindle and acrylic panels). |
| A2 | 12 V vacuum pump | 1 | 25.50 | [SparkFun](https://www.sparkfun.com/vacuum-pump-12v.html) | Same voltage and electrical tabs as the stock CNC spindle, so it drops straight into the spindle terminals. |
| A3 | Suction cup, 0.35 in cup, bellows, 10-32 thread | 1 | 13.50 | [McMaster 3766A135](https://www.mcmaster.com/3766A135/) | Cup diameter ~ size of an HPLC vial cap. |
| A4 | Barbed connector, 1/8 in ID, 10-32 thread | 1 | 2.84 | [McMaster 5058K726](https://www.mcmaster.com/5058K726-5058K222/) | Connects to the suction cup. |
| A5 | Barbed connector, 1/4 in OD, 1/4 in ID | 1 | 4.34 | [McMaster 9406T24](https://www.mcmaster.com/9406T24/) | Step-down adapter. |
| A6 | Muffler | 1 | 5.38 | [McMaster 8457T82](https://www.mcmaster.com/products/8457t82/) | Optional — quiets the pump. |
| A7 | Tubing, 1/4 in ID, 3/8 in OD, ~5 cm | 2 | — | [McMaster 5103K34](https://www.mcmaster.com/5103K34/) | Direct to suction cup / barb. |
| A8 | Tubing, 1/8 in ID, 1/4 in OD, ~30 cm | 1 | — | [McMaster 5103K32](https://www.mcmaster.com/5103K32/) | One end to the suction-cup adapter, one to the muffler. Material must hold a medium vacuum; OD is not critical. |
| A9 | M6×6 mm flathead screws | 4 | — | — | 5–10 mm length is fine. For screwing in deck slots. |
| A10 | M3×6 mm set screws | 5 | — | — | Other M3 lengths / types also work. |
| A11 | M3×6 mm flathead screws | 2 | — | — | |
| A12 | M3 heat-set inserts | 6 | — | — | |

## 3D-printed parts

| # | Part name | Qty | Notes |
| - | --------- | --: | ----- |
| B1 | `deck-slot-standard.stl` | 2 | Screws into the CNC bed. |
| B2 | `vacuum-pump-mounting-plate.stl` | 1 | Mounts the pump onto the moving toolhead. |
| B3 | `vacuum-gripper-toolhead-mount.stl` | 1 | Toolhead mount. |
| B4 | `suction-cup-holder.stl` | 1 | Screws into the toolhead mount and holds the gripper. |
| B5 | `M6-thumb-screws.stl` | 4 | For securing labware into deck slots. Any M6 screw works; based on [McMaster 92545A183](https://www.mcmaster.com/92545A183/). |

## Also required

- A computer (Windows / macOS / Linux) with a USB-A port (or the necessary
  dongle) to talk to the CNC over USB serial.
- Soldering iron for installing the M3 heat-set inserts.
- Allen keys and screwdrivers.

---

## Assembly

### Stage 1 — Base CNC

Build the Genmitsu 3018 per the [SainSmart manual](https://docs.sainsmart.com/article/appuv0ufmb-3018-prover-v-2)
up to section 3, **skipping steps 2.4 (spindle) and 2.5 (acrylic panels)**.

Confirm homing works in [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations)
or another GRBL UI before the Python library ever touches it.

### Stage 2 — Mount the deck

Bolt two `deck-slot-standard.stl` plates (B1) onto the CNC bed with M6×6
flatheads (A9). One slot holds the storage rack (X / O pieces), one holds the
game board. Square them against the X / Y axes before final torque.

### Stage 3 — Build the vacuum gripper

1. Install the M3 heat-set inserts (A12) into `vacuum-gripper-toolhead-mount.stl`
   (B3) and `vacuum-pump-mounting-plate.stl` (B2) with a soldering iron.
2. Screw the suction-cup holder (B4) into the toolhead mount (B3) using M3×6
   flatheads (A11).
3. Thread the suction cup (A3) into the holder. Add the 10-32 → 1/8 in barbed
   connector (A4) on the back of the cup.
4. Bolt the pump mounting plate (B2) onto the CNC's spindle carriage, then bolt
   the pump (A2) onto it.
5. Run a short length of 1/4 in tubing (A7) from the pump outlet to the
   step-down barb (A5), then 1/8 in tubing (A8) from the step-down to the
   suction-cup barb (A4). Add the muffler (A6) on the pump's exhaust if you
   want a quieter rig — use the second piece of 1/4 in tubing (A7).
6. **Wire the pump into the GRBL spindle terminals** (same connector the
   stock spindle uses). Verify polarity by sending `M3 S1000` from Candle —
   the pump should run; `M5` stops it.

### Stage 4 — Calibrate

Run `python z_helper.py` from this directory to find pick / place Z heights,
then copy them into [`tools/cnc_config.yaml`](tools/cnc_config.yaml) under
`z_heights:`.
