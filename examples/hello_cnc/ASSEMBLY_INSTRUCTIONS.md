# Assembly instructions — hello_cnc

Minimum physical setup for verifying the CNC and its USB serial connection.
This is what every example builds on top of.

**Target time:** ~1 hour, once parts are in hand.

Source of truth for this BOM is [hello_cnc_bom.csv](hello_cnc_bom.csv).

---

## Purchased parts

| # | Part | Qty | ~Cost (USD) | Link | Notes |
| - | ---- | --- | ----------- | ---- | ----- |
| A1 | Genmitsu 3018-PROVer V2 CNC | 1 | 256 | [Amazon](https://www.amazon.ca/Genmitsu-3018-PROVer-Beginner-Emergency-Stop-Spoilboard/dp/B0CMTJ6CZC) | Follow the [SainSmart assembly manual](https://docs.sainsmart.com/article/appuv0ufmb-3018-prover-v-2) up to section 3, **skipping steps 2.4 / 2.5** (spindle and acrylic panels — not needed). |

## Also required

- A computer (Windows / macOS / Linux) with a USB-A port (or the necessary
  dongle) to talk to the CNC over USB serial.

---

## Assembly

1. Build the CNC per the SainSmart manual through section 3, skipping the
   spindle install (2.4) and acrylic side panels (2.5).
2. Plug the controller into the host PC via the included USB-A → USB-B cable.
3. Run the [hello_cnc.py](hello_cnc.py) script from the [README](README.md) to
   verify homing, jogging, and the spindle output (M3 / M5) all respond.

If the smoke test passes, you're done — move on to one of the tool-equipped
examples (liquid handling, vacuum pick-and-place, …).
