# Hello CNC

After physically setting up the CNC machine, this does a basic check. Verifies serial connection, homing, a basic move, and spindle on/off.

## Run

```bash
# Edit cnc_config.yaml in this folder (COM port, bounds) first.
python hello_cnc.py
```

Expected: machine homes, moves to vial rack position 1, spins the spindle, returns to origin.
