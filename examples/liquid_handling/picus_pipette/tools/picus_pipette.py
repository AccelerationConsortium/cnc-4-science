"""Picus 2 pipette tool — thin wrapper around the vendored low-level driver.

Adds a ``virtual`` flag for dry-runs and a stable API for protocols. The
underlying ``Picus2`` driver (Sartorius Picus 2 model) lives in
``picus_driver.py``.
"""

from __future__ import annotations

from .picus_driver import Picus2


class PicusPipette:
    """Thin wrapper around Picus2 with optional virtual mode."""

    def __init__(self, com_port: str | None = None, virtual: bool = False, default_speed: int = 5):
        self.com_port = com_port
        self.virtual = virtual
        self.default_speed = default_speed
        self._pip: Picus2 | None = None

    def connect(self):
        if self.virtual:
            print(f"[Pipette] Virtual connect (would use {self.com_port})")
            return
        self._pip = Picus2(port=self.com_port, default_speed=self.default_speed)
        self._pip.open()
        self._pip.run_init()

    def close(self):
        if self.virtual:
            print("[Pipette] Virtual disconnect")
            return
        if self._pip is not None:
            self._pip.close()
            self._pip = None

    def aspirate(self, volume_ul: float, speed: int | None = None):
        if self.virtual:
            print(f"[Pipette] Aspirate {volume_ul}µL (speed={speed or self.default_speed})")
            return
        self._pip.aspirate(volume_ul, speed=speed)

    def dispense(self, volume_ul: float, speed: int | None = None):
        if self.virtual:
            print(f"[Pipette] Dispense {volume_ul}µL (speed={speed or self.default_speed})")
            return
        self._pip.dispense(volume_ul, speed=speed)

    def blow_out(self, speed: int | None = None, delay_ms: int = 3000, go_home: bool = True):
        if self.virtual:
            print(f"[Pipette] Blow-out (delay={delay_ms}ms, go_home={go_home})")
            return
        self._pip.blow_out(speed=speed, delay_ms=delay_ms, go_home=go_home)

    def tip_eject(self):
        if self.virtual:
            print("[Pipette] Tip eject")
            return
        self._pip.tip_eject()

    def home(self):
        if self.virtual:
            print("[Pipette] Home piston")
            return
        self._pip.home()
