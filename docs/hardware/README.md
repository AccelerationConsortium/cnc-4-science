# Hardware documentation — base platform

This directory documents the **shared base machine**: the CNC gantry and the
deck plate that every example mounts onto. Per-tool hardware (vacuum gripper,
Picus pipette mount, etc.) is documented inside each example's own directory.

- [BOM.md](BOM.md) — bill of materials for the base CNC + deck.
- [ASSEMBLY.md](ASSEMBLY.md) — assembly steps for the base CNC + deck.
- [CAD.md](CAD.md) — index of shared CAD files (deck plate, labware).

For per-tool hardware see:

- [examples/vacuum_pick_and_place/HARDWARE.md](../../examples/vacuum_pick_and_place/HARDWARE.md)
- [examples/liquid_handling/HARDWARE.md](../../examples/liquid_handling/HARDWARE.md)

The Python library itself lives in [`src/cnc_machine_core/`](../../src/cnc_machine_core/);
software setup (Python install, config files, Z calibration) is covered in the
[top-level SETUP.md](../SETUP.md), not here.

> **Status: placeholders.** These docs are stubs. Fill them in as the hardware
> design solidifies.
