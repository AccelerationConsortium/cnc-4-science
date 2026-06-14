# Hardware — vacuum pick-and-place

> **Placeholder.** Fill in once the reference build is finalized.

Hardware specific to the vacuum-gripper toolhead used by this example. For the
base CNC, deck plate, and shared platform parts see
[`docs/hardware/`](../../docs/hardware/).

## BOM

| Qty | Part | Vendor | Approx. cost (USD) | Notes |
| --- | ---- | ------ | ------------------ | ----- |
| 1   | Vacuum pump (12 V) | _\<vendor\>_ | _$\<n\>_ | Wired directly to the GRBL spindle terminals (M3 / M5 toggles the pump). |
| 1   | Suction cup, ~5 mm OD | _\<vendor\>_ | _$\<n\>_ | Sized to the tic-tac-toe pieces (or whatever you're picking). |
| 1   | Silicone tubing, 4 mm ID | _\<vendor\>_ | _$\<n\>_ | From pump → gripper. |
| 1   | 3D-printed gripper mount | _self-print, see CAD below_ | _$\<material\>_ | Bolts onto the spindle carriage. |
| 15  | Tic-tac-toe pieces (X / O) | _self-print or wood_ | _$\<n\>_ | Fit the 100 µL custom labware wells. |

## Assembly

1. Print the gripper mount and bolt it to the spindle carriage in place of the
   stock spindle. The suction cup should sit at roughly the same Z as the
   spindle bit it replaces.
2. Glue the suction cup to the bottom of the gripper mount.
3. Cut a length of silicone tubing from the pump outlet to the gripper inlet.
4. Wire the vacuum pump to the GRBL spindle terminals on the controller board.
   Verify polarity — the pump should turn on when GRBL sends `M3` and off on
   `M5`.
5. Run `python z_helper.py` from this directory to calibrate the pick / place
   Z heights, then copy them into `tools/cnc_config.yaml` under `z_heights:`.

## CAD

| File | Description | Print settings | Notes |
| ---- | ----------- | -------------- | ----- |
| _TBD_ | Vacuum gripper mount | 0.2 mm layer, 30% infill, PETG | Mounts to spindle carriage. |
| `custom_labware/storage_15_tuberack_100ul.json` + (CAD TBD) | Storage rack (15 pieces, 5x3) | _\<material\>_ | Holds unplaced X/O pieces. |
| `custom_labware/gameboard_15_tuberack_100ul.json` + (CAD TBD) | Game board (3x3 play area, ignore outer wells) | _\<material\>_ | The actual tic-tac-toe board. |
