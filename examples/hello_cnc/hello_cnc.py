"""Hardware sanity check — run this first after physically setting up the machine.

Verifies serial connection, homing, basic moves, and spindle control.
Edit cnc_config.yaml in this folder (COM port, bounds) before running.

Usage:
    python hello_cnc.py
"""

from pathlib import Path

from cnc_machine_core import CNC_Machine

CONFIG_PATH = Path(__file__).resolve().parent / "cnc_config.yaml"
LOCATIONS_FILE = Path(__file__).resolve().parent / "location_status.yaml"

m = CNC_Machine.from_config(CONFIG_PATH, locations_file=str(LOCATIONS_FILE))

m.connect()  # open persistent connection (optional)
m.home()  # Home the CNC Machine
m.move_to_location(
    "vial_rack", 1, safe=True, speed=2500
)  # Move to vial rack position 1
m.spindle_on(speed=2000)  # Turn on spindle
m.move_to_point(100, 100, -30)  # Move to absolute point (100, 100, -30)
m.spindle_off()  # Turn off spindle
m.origin()  # Move to 0,0,0
m.close()  # Close persistent connection (only if opened)
