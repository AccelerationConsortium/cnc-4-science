# Assembly instructions

> **Placeholder.** Fill in with photos and per-step text once the reference
> build is finalized. Aim for a level of detail where a new student can
> assemble the platform from the box without prior experience.

The build proceeds in three independent stages — finish each before moving on:

1. **Base CNC** — unbox the gantry, mount it on a stable surface, install
   GRBL firmware (if not preloaded), confirm homing with [Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations)
   or another GRBL UI before the Python library ever touches it.
2. **Deck** — install the deck plate onto the CNC bed, square it against the
   X/Y axes, fix it down. Once squared the deck's slot positions are fixed
   forever and you should not need to re-tune them. The numbers in
   [`cnc_4_slot_deck.json`](../../src/cnc_machine_core/deck/cnc_4_slot_deck.json)
   assume the deck is mounted as shown below.
3. **Tool mount** — for each tool you want to swap onto the gantry, install
   its 3D-printed mount on the spindle carriage, then run that tool's
   `z_helper.py` to calibrate Z heights. See the per-example READMEs:
   - [Vacuum gripper](../../examples/vacuum_pick_and_place/README.md)
   - [Picus pipette](../../examples/liquid_handling/README.md)

## Stage 1 — Base CNC

_TODO: photos, wiring, where the USB cable plugs in, what to set in Candle,
how to confirm the limit switches work, how to set work-zero._

## Stage 2 — Deck

_TODO: how the deck is squared and fastened to the CNC bed, what bolts/inserts
are used, photo of the mounted deck with slot 1 labeled, how to verify slot
positions match `cnc_4_slot_deck.json` (jog to each corner, read MPos)._

## Stage 3 — Tool mount

_TODO: for each tool, photos of the assembled mount, wiring (e.g. vacuum pump
to GRBL spindle terminals), XY offset measurement procedure, link to the
tool-specific README for Z calibration._

## Safety

_TODO: emergency-stop location, what to do if a tool crashes into the deck,
when to power-cycle vs re-home, GRBL alarm states._
