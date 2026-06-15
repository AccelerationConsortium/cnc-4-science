# Assembly instructions — liquid handling (Sartorius Picus 2)

Full hardware build for the Picus-pipette serial-dilution example.

**Target time:** ~1 hour, once parts are in hand and 3D-printed.

Source of truth for this BOM is [liquid_handling_CNC_demo_bom.csv](liquid_handling_CNC_demo_bom.csv).

When you're done here, jump back to the [README](README.md) for the software
setup (venv → `pip install` → configure YAML → run).

---

## Purchased parts

| # | Part | Qty | ~Cost (USD) | Link | Notes |
| - | ---- | --: | ----------: | ---- | ----- |
| A1 | Genmitsu 3018-PROVer V2 CNC | 1 | 256 | [Amazon](https://www.amazon.ca/Genmitsu-3018-PROVer-Beginner-Emergency-Stop-Spoilboard/dp/B0CMTJ6CZC) | Follow the [SainSmart assembly manual](https://docs.sainsmart.com/article/appuv0ufmb-3018-prover-v-2) up to section 3, skipping steps 2.4 / 2.5 (spindle and acrylic panels). |
| A2 | Sartorius Picus 2 — 5000 µL single-channel pipette | 1 | 1190 | [Sartorius](https://shop.sartorius.com/us/p/picus-2-electronic-single-channel-pipette/LH-747101) | |
| A3 | Sartorius 5000 µL Optifit tips (bag of 100) | 1 | 25.40 | [Sartorius](https://shop.sartorius.com/us/p/optifit-non-sterile-pipette-tips-bulk-in-a-bag-qty-100/Bagged-Pipette-Tip-150mm) | |
| A4 | Opentrons Tough 4-well reservoir (72 mL) | 1 | 6.80 | [Opentrons](https://opentrons.com/products/opentrons-tough-72-ml-4-well-reservoir-25-count) | Sold in a minimum qty of 25. |
| A5 | Corning 24-well plate | 1 | 3.75 | [Corning](https://ecatalog.corning.com/life-sciences/b2c/US/en/Microplates/Assay-Microplates/96-Well-Microplates/Costar%C2%AE-Multiple-Well-Cell-Culture-Plates/p/3738) | Any vendor's 24-well SBS plate should work. Link is min. qty of 100. |
| A7 | M6×10 mm flathead screws | 8 | — | — | For screwing in deck slots. |
| A8 | M5×25 mm panhead screws | 8 | — | — | For Z-offset spacers. |
| A9 | M5 nuts | 8 | — | — | For Z-offset spacers. |
| A10 | Food colouring (water-based) | 1 | — | [Amazon](https://www.amazon.ca/Club-House-Food-Colour-Preparation/dp/B00HVVNFVW) | Any colour. |

## 3D-printed parts

| # | Part name | Qty | Notes |
| - | --------- | --: | ----- |
| B1 | `100mm-z-spacer.stl` | 2 | Uses M5 hardware to elevate the XZ carriage. |
| B2 | `deck-slot-5mm-taller.stl` | 1 | Installed in deck slot 1. |
| B3 | `deck-slot-standard.stl` | 3 | Installed in deck slots 2–4. |
| B4 | `sartorius_24_tiprack_5000ul.stl` | 2 | Custom 24-tip rack. |
| B5 | `sartorius-5000uL-pipette-tool-holder-A.stl` | 1 | Two-part toolhead mount that clamps around the pipette. |
| B6 | `sartorius-5000uL-pipette-tool-holder-B.stl` | 1 | Two-part toolhead mount that clamps around the pipette. |
| B7 | `M6-thumb-screws.stl` | 8 | For securing labware into deck slots. Any M6 screw works; based on [McMaster 92545A183](https://www.mcmaster.com/92545A183/). |

## Also required

- A computer (Windows / macOS / Linux) with a USB-A port (or the necessary
  dongle) to talk to the CNC over USB serial.
- Tap water for the dilutions.
- Allen keys and screwdrivers.

---

## Assembly

### Stage 1 — Base CNC

Build the Genmitsu 3018 per the [SainSmart manual](https://docs.sainsmart.com/article/appuv0ufmb-3018-prover-v-2)
up to section 3, **skipping steps 2.4 (spindle) and 2.5 (acrylic panels)** —
they aren't needed for this build.

Confirm homing works in [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations)
or another GRBL UI before the Python library ever touches it.

### Stage 2 — Elevate the gantry and mount the deck

1. Install the two `100mm-z-spacer.stl` parts (B1) between the XZ carriage and
   the gantry uprights using M5×25 panhead screws + M5 nuts (A8, A9). This
   gives the Picus tip clearance over the deck.
2. Bolt the four deck slot plates (B2 ×1 in slot 1, B3 ×3 in slots 2–4) onto
   the CNC bed with M6×10 flatheads (A7). Square them against the X / Y axes
   before final torque — once squared, slot positions are fixed.

### Stage 3 — Mount the Picus pipette

1. Clamp the two-part pipette holder (B5 + B6) around the Picus body.
2. Bolt the assembly onto the spindle carriage in place of the stock spindle.
   The tip should hang below the gantry far enough to reach the deepest well
   with a few mm of clearance.
3. Plug the Picus USB cable into the host PC. Note the COM port name and set
   it in [`tools/picus_config.yaml`](tools/picus_config.yaml).

### Stage 4 — Calibrate

Measure aspirate / dispense / tip-pickup / tip-eject Z heights by hand:
jog Z with a GRBL UI (e.g. [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations))
until the tip kisses the target surface, then write the numbers into
[`tools/cnc_config.yaml`](tools/cnc_config.yaml) under `z_heights:`. See
[docs/SETUP.md §4](../../docs/SETUP.md#4-calibrate-z-heights) for the
rationale and the recommended labels.
