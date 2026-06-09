"""Vacuum gripper tool template — standard with the CNC gantry.

Uses the CNC spindle output to toggle a vacuum pump on/off.
Copy this into your application's tools directory and calibrate offsets
in your tool_definitions.json.
"""

import time


class VacuumGripper:
    """Vacuum gripper controlled via CNC spindle (M3/M5)."""

    def __init__(self, cnc_machine, tool_config):
        self.cnc = cnc_machine
        self.offset = tool_config.get("offset", {"x": 0, "y": 0, "z": 0})
        self.spindle_speed = tool_config.get("spindle_speed_rpm", 1000)

    def vacuum_on(self):
        """Turn on vacuum via CNC spindle."""
        self.cnc.follow_gcode_path(f"M3 S{self.spindle_speed}\n")

    def vacuum_off(self):
        """Turn off vacuum by stopping spindle."""
        self.cnc.follow_gcode_path("M5\n")

    def pick(self, x, y, z, speed=1000):
        """Move to position and pick up an object.

        Args:
            x, y, z: Absolute CNC coordinates (tool offset already applied).
            speed: Movement speed in mm/min.
        """
        self.cnc.move_to_point_safe(x, y, z, speed=speed)
        time.sleep(1)
        self.vacuum_on()

    def place(self, x, y, z, speed=1000):
        """Move to position and release an object.

        Args:
            x, y, z: Absolute CNC coordinates (tool offset already applied).
            speed: Movement speed in mm/min.
        """
        self.cnc.move_to_point_safe(x, y, z, speed=speed)
        time.sleep(1)
        self.vacuum_off()
