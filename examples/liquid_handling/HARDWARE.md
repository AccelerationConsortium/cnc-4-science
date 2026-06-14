# Hardware — liquid handling (Sartorius Picus)

> **Placeholder.** Fill in once the reference build is finalized.

Hardware specific to the Picus-pipette toolhead used by this example. For the
base CNC, deck plate, and shared platform parts see
[`docs/hardware/`](../../docs/hardware/).

## BOM

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Sartorius Picus electronic pipette | _Sartorius_ | _$$$_ | Verified with the 5000 µL head. |
| 1   | Picus USB cable | _Sartorius_ | _$\<n\>_ | For serial control from the host PC. |
| 1   | 3D-printed pipette holster | _self-print, see CAD below_ | _$\<material\>_ | Clamps the Picus body to the spindle carriage. |
| _N_ | Picus-compatible tips | _Sartorius_ | _$\<n\>/box_ | Volume matches your protocol. |
| _N_ | Standard SBS labware (source / dest plates) | _\<vendor\>_ | _$\<n\>_ | Sourced from `opentrons-shared-data` definitions; see [`deck_preset.yaml`](deck_preset.yaml). |

## Assembly

1. Print the Picus holster and bolt it to the spindle carriage in place of the
   stock spindle.
2. Slide the Picus into the holster and tighten the clamp; the tip should hang
   below the gantry by enough to reach the deepest labware well plus a few mm
   clearance.
3. Plug the Picus USB cable into the host PC. Confirm the port name and set it
   in `tools/picus_config.yaml`.
4. Run `python z_helper.py` from this directory to calibrate aspirate /
   dispense / tip-pickup / tip-eject Z heights, then copy them into
   `tools/cnc_config.yaml` under `z_heights:`.

## CAD

| File | Description | Print settings | Notes |
| ---- | ----------- | -------------- | ----- |
| _TBD_ | Picus pipette holster | 0.2 mm layer, 30% infill, PETG | Mounts to spindle carriage. Match clamp geometry to your Picus model. |
