# CAD files — base platform

> **Placeholder.** Per-tool CAD (gripper mount, pipette holster, etc.) lives
> next to each example:
> [vacuum_pick_and_place](../../examples/vacuum_pick_and_place/HARDWARE.md) ·
> [liquid_handling](../../examples/liquid_handling/HARDWARE.md).

Source files (`.f3d`, `.step`, `.dxf`) are stored alongside the print-ready
exports (`.stl`) so design history is preserved.

## Deck

| File | Description | Material | Notes |
| ---- | ----------- | -------- | ----- |
| _TBD_ | 4-slot SBS deck plate | _PETG / aluminum_ | Matches [`cnc_4_slot_deck.json`](../../src/cnc_machine_core/deck/cnc_4_slot_deck.json). |

## Shared labware

Custom labware definitions and their CAD live next to the JSON, under
[`src/cnc_machine_core/labware/`](../../src/cnc_machine_core/labware/).

| Labware JSON | CAD file | Description |
| ------------ | -------- | ----------- |
| [`vialtrayholder_25_tuberack_1000ul.json`](../../src/cnc_machine_core/labware/vialtrayholder_25_tuberack_1000ul.json) | `labware/cad/vialtrayholder_25_tuberack_1000ul.{stl,f3d}` | 25-position HPLC vial rack. |

## Print settings (default)

Unless otherwise noted, every printed part is designed for:

- Printer: _Prusa MK3S / Bambu Lab P1S / equivalent FDM_
- Material: _PETG_
- Layer height: _0.2 mm_
- Infill: _30%_
- Support: _only where called out per-file_

Aluminum parts (deck plate, brackets) are cut from 6 mm stock unless noted.
