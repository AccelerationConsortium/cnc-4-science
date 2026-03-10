class VialCapper:
    """Tool for pressing caps onto vials using Z-axis motion."""

    def __init__(self, cnc_machine, tool_config):
        self.cnc = cnc_machine
        self.offset = tool_config.get("offset", {"x": 0, "y": 0, "z": 0})
        params = tool_config.get("parameters", {})
        self.press_depth = params.get("press_depth_mm", 5.0)
        self.press_speed = params.get("press_speed", 500)

    def press(self, x, y, z):
        """Move to position and press down to cap a vial.

        Args:
            x, y, z: Target position (already resolved to absolute CNC coordinates).
        """
        press_x = x + self.offset["x"]
        press_y = y + self.offset["y"]
        press_z = z + self.offset["z"]

        self.cnc.move_to_point_safe(press_x, press_y, press_z, speed=self.press_speed)
        target_z = press_z - self.press_depth
        self.cnc.move_to_point(z=target_z, speed=self.press_speed)
        self.cnc.move_to_point(z=press_z, speed=self.press_speed)

    def press_well(self, x, y, z):
        """Alias for press() when targeting a well/vial position."""
        self.press(x, y, z)
