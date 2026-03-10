try:
    from vernier_drop_counter import DripCounter
    from runze_valve import RunzeValve
except ImportError:
    DripCounter = None
    RunzeValve = None


class DropCounter:
    """Vernier drop counter with integrated Runze valve for fraction collection.

    Wraps the Vernier DripCounter sensor and a Runze multi-port valve to
    control fluid routing between collection and waste lines.
    """

    def __init__(self, cnc_machine, tool_config):
        self.cnc = cnc_machine
        self.offset = tool_config.get("offset", {"x": 0, "y": 0, "z": 0})

        params = tool_config.get("parameters", {})
        if DripCounter is None:
            raise ImportError(
                "vernier_drop_counter package is required for DropCounter"
            )
        if RunzeValve is None:
            raise ImportError("runze_valve package is required for DropCounter")
        self.sensor = DripCounter(sensor_id=params.get("sensor_id", 1))
        self.valve = RunzeValve(
            com_port=params.get("valve_port", "COM9"),
            address=params.get("valve_address", 0),
            num_port=params.get("valve_num_ports", 10),
        )
        self.collection_port = params.get("collection_port", 3)
        self.waste_port = params.get("waste_port", 6)

    def set_collection(self):
        """Route fluid to the collection line."""
        self.valve.set_current_port(self.collection_port)

    def set_waste(self):
        """Route fluid to the waste line."""
        self.valve.set_current_port(self.waste_port)

    def wait_for_drops(self, count, timeout=120, poll_interval=20):
        """Block until the specified number of drops have been counted.

        Returns:
            True if drops were counted within timeout, False otherwise.
        """
        return self.sensor.wait_for_drops(
            count, timeout=timeout, poll_interval=poll_interval
        )

    def collect_fraction(
        self,
        x,
        y,
        z,
        drop_count,
        rinse_drops=20,
        timeout=120,
        poll_interval=20,
        speed=2500,
    ):
        """Run a full fraction collection cycle at the given position.

        1. Move to waste position and rinse collection tubing.
        2. Move to target well/vial.
        3. Collect the specified number of drops.
        4. Return valve to waste.

        Args:
            x, y, z: Target position (absolute CNC coordinates).
            drop_count: Number of drops to collect.
            rinse_drops: Number of drops to flush through tubing first.
            timeout: Max seconds to wait for drops.
            poll_interval: Seconds between drop count polls.
            speed: CNC movement speed in mm/min.

        Returns:
            True if collection succeeded, False if timed out.
        """
        collect_x = x + self.offset["x"]
        collect_y = y + self.offset["y"]
        collect_z = z + self.offset["z"]

        # Rinse
        self.set_collection()
        self.wait_for_drops(rinse_drops, timeout=timeout, poll_interval=poll_interval)
        self.set_waste()

        # Move to target
        self.cnc.move_to_point_safe(collect_x, collect_y, collect_z, speed=speed)

        # Collect
        self.set_collection()
        success = self.wait_for_drops(
            drop_count, timeout=timeout, poll_interval=poll_interval
        )
        self.set_waste()

        return success
