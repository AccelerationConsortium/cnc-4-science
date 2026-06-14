# Assembly instructions — base platform

> **Placeholder.** Per-tool assembly lives next to each example:
> [vacuum_pick_and_place](../../examples/vacuum_pick_and_place/HARDWARE.md) ·
> [liquid_handling](../../examples/liquid_handling/HARDWARE.md).

The base platform comes together in two stages. Finish both before installing
any tool.

## Stage 1 — Base CNC

_TODO: photos, wiring, where the USB cable plugs in, what to set in
[Candle](https://docs.sainsmart.com/article/bj9o96wcbc-how-to-set-up-use-candle-for-multiple-operations),
how to confirm the limit switches work, how to set work-zero._

1. Unbox the gantry and mount it on a stable surface.
2. Confirm GRBL is preloaded (most Genmitsu kits ship preloaded). If not, flash
   GRBL before continuing.
3. Confirm homing works in Candle (or another GRBL UI) before the Python
   library ever touches it.

## Stage 2 — Deck

_TODO: how the deck is squared and fastened to the CNC bed, what bolts /
inserts are used, photo of the mounted deck with slot 1 labeled, how to verify
slot positions match
[`cnc_4_slot_deck.json`](../../src/cnc_machine_core/deck/cnc_4_slot_deck.json)
(jog to each corner, read MPos)._

1. Install the deck plate onto the CNC bed.
2. Square it against the X / Y axes and fix it down. Once squared, slot
   positions are fixed forever and should not need re-tuning.

## Stage 3 — Tool mount

For each tool, see that example's `HARDWARE.md`. Each tool has its own
mounting procedure, its own Z calibration step (`python z_helper.py`), and its
own wiring.

## Safety

_TODO: emergency-stop location, what to do if a tool crashes into the deck,
when to power-cycle vs re-home, GRBL alarm states._
