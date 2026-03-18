from cnc_machine_core import CNC_Machine

"""Hardware sanity check — run this first after physically setting up the machine.

Verifies serial connection, homing, basic moves, and spindle control.
Update COM port and bounds to match your setup before running.

Usage:
    python hardware_check.py
"""
m = CNC_Machine(com="COM3", virtual=False, locations_file="location_status.yaml")

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
