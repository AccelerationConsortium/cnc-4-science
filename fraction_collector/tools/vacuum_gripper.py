class VacuumGripper:
    """Vacuum gripper tool that uses the CNC spindle to toggle vacuum."""

    def __init__(self, cnc_machine, tool_config):
        self.cnc = cnc_machine
        self.offset = tool_config.get("offset", {"x": 0, "y": 0, "z": 0})
        params = tool_config.get("parameters", {})
        self.spindle_speed = params.get("spindle_speed_rpm", 1000)
        self.pickup_z_offset = params.get("pickup_z_offset_mm", -5.0)
        self.place_z_offset = params.get("place_z_offset_mm", -3.0)

    def vacuum_on(self):
        """Turn on vacuum via CNC spindle."""
        self.cnc.follow_gcode_path(f"M3 S{self.spindle_speed}\n")

    def vacuum_off(self):
        """Turn off vacuum by stopping spindle."""
        self.cnc.follow_gcode_path("M5\n")

    def pick(self, x, y, z, speed=1000):
        """Pick up an object at the given position.

        Args:
            x, y, z: Target position (absolute CNC coordinates).
            speed: Movement speed in mm/min.
        """
        pick_x = x + self.offset["x"]
        pick_y = y + self.offset["y"]
        pick_z = z + self.offset["z"]

        self.cnc.move_to_point_safe(pick_x, pick_y, pick_z, speed=speed)
        self.vacuum_on()
        self.cnc.move_to_point(z=pick_z + self.pickup_z_offset, speed=speed)
        self.cnc.move_to_point(z=pick_z, speed=speed)

    def place(self, x, y, z, speed=1000):
        """Place an object at the given position.

        Args:
            x, y, z: Target position (absolute CNC coordinates).
            speed: Movement speed in mm/min.
        """
        place_x = x + self.offset["x"]
        place_y = y + self.offset["y"]
        place_z = z + self.offset["z"]

        self.cnc.move_to_point_safe(place_x, place_y, place_z, speed=speed)
        self.cnc.move_to_point(z=place_z + self.place_z_offset, speed=speed)
        self.vacuum_off()
        self.cnc.move_to_point(z=place_z, speed=speed)
