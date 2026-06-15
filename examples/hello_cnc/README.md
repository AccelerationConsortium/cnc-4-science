# Hello CNC

The hardware smoke test. Run this **right after assembling the machine** and
**before any protocol** to verify the serial connection, homing, a basic
movement, spindle on/off, and the work-zero return.

If this passes, your CNC + COM port + bounds + Python install are all good
and you can move on to a real protocol like
[liquid_handling/](../liquid_handling/) or
[vacuum_pick_and_place/](../vacuum_pick_and_place/).

For the hardware build itself (~1 hour), see
[ASSEMBLY_INSTRUCTIONS.md](ASSEMBLY_INSTRUCTIONS.md).

## Run

```bash
# 1. Create + activate a virtual environment (from the repo root)
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows
# source .venv/bin/activate      # Linux / macOS

# 2. Install cnc-4-science
pip install cnc-4-science

# 3. Edit cnc_config.yaml in this folder — set your COM port and travel bounds.
#    (See docs/SETUP.md §0 for how to measure your bounds in Candle.)

# 4. Run
python hello_cnc.py
```

**Expected:** the machine homes, moves to vial-rack position 1, spins the
spindle for a moment, returns to the origin, and exits cleanly.

If anything fails, fix `cnc_config.yaml` (port / bounds) and re-run — do not
move on to a real protocol until this passes.
