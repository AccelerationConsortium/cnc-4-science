# Bill of Materials (BOM)

> **Placeholder.** Fill in as the reference build is finalized. The intent of
> this document is to be specific enough that someone with no prior context can
> reproduce the platform by ordering everything listed here.

## Base CNC

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Genmitsu 3018-PROVer / equivalent GRBL CNC | _e.g. SainSmart_ | _$300_ | Travel ~300x180x45 mm; verify your bounds in `tools/cnc_config.yaml`. |
| 1   | Power supply (24 V, included with most kits) | _\<vendor\>_ | _included_ | |
| 1   | USB-A to USB-B cable | _generic_ | _$5_ | Long enough to reach the host PC. |

## Deck

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| _TBD_ | Deck plate (3D-printed or aluminum) | _self-print, see [CAD.md](CAD.md)_ | _$\<material\>_ | Footprint matches `cnc_4_slot_deck.json`. |
| _TBD_ | SBS-format labware spacers / clips | _\<vendor\>_ | _$\<n\>_ | Hold labware square in each slot. |

## Per-tool add-ons

For each toolhead you mount on the gantry, list the parts here under a
sub-heading. Mirror the structure used in
[`examples/vacuum_pick_and_place/`](../../examples/vacuum_pick_and_place/) and
[`examples/liquid_handling/`](../../examples/liquid_handling/).

### Vacuum gripper (pick-and-place example)

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Vacuum pump (12 V) | _\<vendor\>_ | _$\<n\>_ | Wired to GRBL spindle terminals. |
| 1   | Suction cup, ~5 mm OD | _\<vendor\>_ | _$\<n\>_ | Sized to the piece being picked. |
| 1   | Silicone tubing, 4 mm ID | _\<vendor\>_ | _$\<n\>_ | |
| 1   | 3D-printed gripper mount | _self-print_ | _$\<material\>_ | STL in [CAD.md](CAD.md). |

### Liquid handling (Picus pipette example)

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Sartorius Picus electronic pipette | _Sartorius_ | _$$\$_ | Verified with the 5000 µL head. |
| 1   | Picus USB cable | _Sartorius_ | _$\<n\>_ | |
| 1   | 3D-printed pipette holster | _self-print_ | _$\<material\>_ | STL in [CAD.md](CAD.md). |

## Total estimated cost

| Build | Approx. (USD) |
| ----- | ------------- |
| Base machine only        | _$300_ |
| + Vacuum pick-and-place  | _$\<n\>_ |
| + Liquid handling        | _$\<n\>_ |
