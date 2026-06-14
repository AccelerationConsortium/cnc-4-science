# Hardware documentation

This directory holds everything you need to **build the physical machine** that
the `cnc_machine_core` library drives. It's organized as follows:

- [BOM.md](BOM.md) — bill of materials. Every part to buy, where to buy it,
  approximate cost, and substitution notes.
- [ASSEMBLY.md](ASSEMBLY.md) — step-by-step assembly instructions for the base
  CNC + the deck + any per-tool mounting.
- [CAD.md](CAD.md) — index of CAD / 3D-printable files (`.f3d`, `.step`, `.stl`,
  `.dxf`) checked into the repo, plus print/cut settings.

The Python library itself lives in [`src/cnc_machine_core/`](../../src/cnc_machine_core/);
software setup (Python install, config files, Z calibration) is covered in the
[top-level SETUP.md](../SETUP.md), not here.

> **Status: placeholders.** These docs are stubs. Fill them in as the hardware
> design solidifies.
