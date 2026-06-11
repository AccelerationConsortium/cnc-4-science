"""Vacuum gripper tool — uses the CNC's spindle output as the vacuum on/off.

No separate serial port: the vacuum pump is wired to the CNC controller's
spindle output and toggled via GRBL ``M3 S<rpm>`` / ``M5``. The wrapper holds
a reference to the ``CNC_Machine`` and forwards engage/release through it.
A ``virtual`` flag mirrors the pattern in :mod:`tools.picus_pipette` so
protocols can dry-run without hardware.
"""

from __future__ import annotations

import time


class VacuumGripper:
    """Thin wrapper that drives a vacuum pump via the CNC spindle output."""

    def __init__(
        self,
        cnc,
        virtual: bool = False,
        vacuum_rpm: int = 2500,
        grip_delay_s: float = 0.5,
        place_delay_s: float = 3.5,
        offset: dict | None = None,
    ):
        self.cnc = cnc
        self.virtual = virtual
        self.vacuum_rpm = vacuum_rpm
        self.grip_delay_s = grip_delay_s
        self.place_delay_s = place_delay_s
        self.offset = offset or {"x": 0.0, "y": 0.0, "z": 0.0}

    # --- lifecycle (kept for symmetry with PicusPipette) --------------------

    def connect(self):
        if self.virtual:
            print("[Vacuum] Virtual connect")
            return
        # No separate channel — CNC owns the serial port.

    def close(self):
        # Always make sure vacuum is off when shutting down.
        self.release()

    # --- primitives ---------------------------------------------------------

    def engage(self, rpm: int | None = None):
        """Turn vacuum on at the given (or default) RPM and settle."""
        speed = rpm if rpm is not None else self.vacuum_rpm
        if self.virtual:
            print(f"[Vacuum] Engage (rpm={speed}, settle={self.grip_delay_s}s)")
            time.sleep(self.grip_delay_s)
            return
        self.cnc.spindle_on(speed=speed)
        time.sleep(self.grip_delay_s)

    def release(self):
        """Turn vacuum off and let the piece drop."""
        if self.virtual:
            print(f"[Vacuum] Release (settle={self.place_delay_s}s)")
            time.sleep(self.place_delay_s)
            return
        self.cnc.spindle_off()
        time.sleep(self.place_delay_s)
