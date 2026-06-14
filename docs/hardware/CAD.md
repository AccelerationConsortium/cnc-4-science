# CAD files

> **Placeholder.** Index of every CAD / 3D-printable asset checked into the
> repo, plus print/cut settings. Update as new mounts and labware are added.

Source files (`.f3d`, `.step`, `.dxf`) are stored alongside the print-ready
exports (`.stl`) so the design history is preserved.

## Deck

| File | Description | Material | Notes |
| ---- | ----------- | -------- | ----- |
| _TBD_ | 4-slot SBS deck plate | _PETG / aluminum_ | Matches [`cnc_4_slot_deck.json`](../../src/cnc_machine_core/deck/cnc_4_slot_deck.json). |

## Labware

Custom labware definitions and their CAD live next to the JSON, under
[`src/cnc_machine_core/labware/`](../../src/cnc_machine_core/labware/).

| Labware JSON | CAD file | Description |
| ------------ | -------- | ----------- |
| [`vialtrayholder_25_tuberack_1000ul.json`](../../src/cnc_machine_core/labware/vialtrayholder_25_tuberack_1000ul.json) | `labware/cad/vialtrayholder_25_tuberack_1000ul.{stl,f3d}` | 25-position HPLC vial rack. |
| _\<add more as you create them\>_ | | |

## Tool mounts

| Tool | CAD file | Print settings | Notes |
| ---- | -------- | -------------- | ----- |
| Vacuum gripper | _TBD_ | _0.2 mm layer, 30% infill_ | Mounts to spindle carriage; suction cup glued to bottom. |
| Picus pipette holster | _TBD_ | _0.2 mm layer, 30% infill_ | Clamps Picus body to spindle carriage. |

## Print settings (default)

Unless otherwise noted, every printed part is designed for:

- Printer: _Prusa MK3S / Bambu Lab P1S / equivalent FDM_
- Material: _PETG_
- Layer height: _0.2 mm_
- Infill: _30%_
- Support: _only where called out per-file_

Aluminum parts (deck plate, brackets) are cut from 6 mm stock unless noted.
