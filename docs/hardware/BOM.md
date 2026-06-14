# Bill of Materials — base platform

> **Placeholder.** Per-tool BOMs live next to each example:
> [vacuum_pick_and_place](../../examples/vacuum_pick_and_place/HARDWARE.md) ·
> [liquid_handling](../../examples/liquid_handling/HARDWARE.md).

## Base CNC

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Genmitsu 3018-PROVer / equivalent GRBL CNC | _e.g. SainSmart_ | _$300_ | Travel ~300x180x45 mm; verify your bounds in each example's `tools/cnc_config.yaml`. |
| 1   | Power supply (24 V, included with most kits) | _\<vendor\>_ | _included_ | |
| 1   | USB-A to USB-B cable | _generic_ | _$5_ | Long enough to reach the host PC. |

## Deck

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| _TBD_ | Deck plate (3D-printed or aluminum) | _self-print, see [CAD.md](CAD.md)_ | _$\<material\>_ | Footprint matches [`cnc_4_slot_deck.json`](../../src/cnc_machine_core/deck/cnc_4_slot_deck.json). |
| _TBD_ | SBS-format labware spacers / clips | _\<vendor\>_ | _$\<n\>_ | Hold labware square in each slot. |

## Estimated cost (base only)

| Build | Approx. (USD) |
| ----- | ------------- |
| Base machine + deck | _$300 + materials_ |
