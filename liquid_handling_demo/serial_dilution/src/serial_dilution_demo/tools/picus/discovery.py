"""USB auto-detection for the Sartorius Picus 2 pipette."""

from __future__ import annotations

from serial.tools import list_ports

_MATCH_SUBSTRINGS = ("picus", "sartorius", "liquid handling")


def _port_fields(info) -> tuple[str, ...]:
    return tuple(
        f for f in (
            getattr(info, "product", None),
            getattr(info, "description", None),
            getattr(info, "manufacturer", None),
            getattr(info, "interface", None),
            getattr(info, "name", None),
        ) if f
    )


def find_pipette_port() -> str | None:
    """Return the first port matching a Picus 2 description, or None."""
    for info in list_ports.comports():
        for field in _port_fields(info):
            lower = field.lower()
            if any(sub in lower for sub in _MATCH_SUBSTRINGS):
                return info.device
    return None


def list_serial_ports() -> list[tuple[str, str]]:
    """Return (device, description) for every available serial port."""
    return [(p.device, p.description or "") for p in list_ports.comports()]
