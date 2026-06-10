"""Sartorius Picus 2 electronic pipette driver.

Speaks the line-based JSON command protocol over a serial port at 230400 baud.
Works identically for USB-CDC (the pipette's Micro-USB port) and Bluetooth SPP.

Usage:
    from tools.picus_driver import Picus2

    with Picus2(port="COM3") as pip:
        pip.run_init()
        pip.aspirate(500)
        pip.dispense(500)
        pip.blow_out()
        pip.tip_eject()

Volumes are in microlitres. Speeds are 1 (slowest) to 9 (fastest).
"""

from __future__ import annotations

import itertools
import json
import logging
import threading
import time
from typing import Self

import serial


# --- Wire protocol primitives ------------------------------------------------

TERMINATOR = b"\r\n"
BAUDRATE = 230400

_ENVELOPE_TOKENS = frozenset({"ACK", "BEGIN", "END"})

RESULT_OK = "OK"
RESULT_CODES = frozenset(
    {
        "OK",
        "FULL",
        "SYNTAX_ERROR",
        "ERROR_PARSING",
        "UNKNOWN_COMMAND",
        "MISSING_PARAMETERS",
        "ERR_RANGE_PARAMETERS",
        "CHK_ERROR",
        "NOT_ALLOWED",
        "FAILED",
        "MOTOR_CONTROL_ABORTED",
    }
)


def build_command(no: int, data: str, **extra: object) -> bytes:
    """Build a CRLF-terminated JSON command frame."""
    payload: dict[str, object] = {"no": no, "data": data}
    payload.update(extra)
    return json.dumps(payload, separators=(",", ":")).encode("ascii") + TERMINATOR


def classify_line(line: str, expected_no: int) -> tuple[str, str | None]:
    """Classify one received line into (kind, value)."""
    stripped = line.strip()
    if not stripped:
        return ("ignore", None)
    parts = stripped.split()
    head = parts[0]
    if head in _ENVELOPE_TOKENS:
        return ("envelope", None)
    if head in RESULT_CODES:
        if len(parts) >= 2:
            try:
                no = int(parts[1])
            except ValueError:
                return ("response", stripped)
            if no == expected_no:
                return ("result", head)
            return ("result_other", head)
        return ("result", head)
    return ("response", stripped)


# --- Driver ------------------------------------------------------------------

log = logging.getLogger(__name__)


class PicusError(Exception):
    """Base exception for the Picus 2 driver."""


class PicusConnectionError(PicusError):
    """Failed to open or communicate with the pipette."""


class PicusCommandError(PicusError):
    """Pipette returned a non-OK result for a command."""

    def __init__(self, result: str, command: str, no: int) -> None:
        self.result = result
        self.command = command
        self.no = no
        super().__init__(f"{command!r} (no={no}) -> {result}")


def _clamp_speed(speed: int) -> int:
    if not 1 <= int(speed) <= 9:
        raise ValueError(f"speed must be in 1..9, got {speed}")
    return int(speed)


def _vol(volume_ul: float) -> int:
    if float(volume_ul) < 0:
        raise ValueError(f"volume must be non-negative, got {volume_ul}")
    return int(round(float(volume_ul)))


class Picus2:
    """Connected Sartorius Picus 2 pipette."""

    def __init__(
        self,
        port: str,
        *,
        baudrate: int = BAUDRATE,
        timeout: float = 0.2,
        command_timeout: float = 30.0,
        default_speed: int = 5,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._command_timeout = command_timeout
        self._default_speed = _clamp_speed(default_speed)
        self._serial: serial.Serial | None = None
        self._counter = itertools.count(1)
        self._lock = threading.Lock()

    def open(self) -> None:
        if self._serial is not None:
            return
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self._timeout,
                write_timeout=1.0,
            )
        except serial.SerialException as e:
            raise PicusConnectionError(f"could not open {self._port}: {e}") from e
        try:
            self._serial.reset_input_buffer()
            self._send_raw("AUTO 1", timeout=2.0)
            self._enable_motor_control_with_confirm()
        except Exception:
            self._serial.close()
            self._serial = None
            raise

    def close(self) -> None:
        ser = self._serial
        if ser is None:
            return
        try:
            self._send_raw("ENABLE_MOTOR_CONTROL 0", timeout=2.0)
        except (PicusError, serial.SerialException) as e:
            log.debug("ignored error leaving protocol mode: %s", e)
        try:
            ser.close()
        except serial.SerialException:
            pass
        self._serial = None

    def __enter__(self) -> Self:
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _enable_motor_control_with_confirm(
        self,
        *,
        mode: int = 2,
        timeout: float = 10.0,
        tap_interval: float = 0.4,
    ) -> None:
        ser = self._serial
        if ser is None:
            raise PicusError("pipette is not open")
        enable_no = next(self._counter)
        enable_frame = build_command(
            enable_no, f"ENABLE_MOTOR_CONTROL {int(mode)}"
        )
        deadline = time.monotonic() + timeout
        with self._lock:
            try:
                ser.write(enable_frame)
                ser.flush()
            except serial.SerialException as e:
                raise PicusConnectionError(f"write failed: {e}") from e
            last_tap = 0.0
            while True:
                now = time.monotonic()
                if now >= deadline:
                    raise PicusError(
                        "timeout enabling motor control"
                        " (no touchscreen confirmation)"
                    )
                if now - last_tap >= tap_interval:
                    button_no = next(self._counter)
                    button_frame = (
                        json.dumps(
                            {"no": button_no, "button": "TRIGGER_BUTTON_RIGHT"},
                            separators=(",", ":"),
                        ).encode("ascii")
                        + TERMINATOR
                    )
                    try:
                        ser.write(button_frame)
                        ser.flush()
                    except serial.SerialException as e:
                        raise PicusConnectionError(f"write failed: {e}") from e
                    last_tap = now
                try:
                    raw = ser.readline()
                except serial.SerialException as e:
                    raise PicusConnectionError(f"read failed: {e}") from e
                if not raw:
                    continue
                line = raw.decode("ascii", errors="replace")
                kind, value = classify_line(line, enable_no)
                if kind == "result":
                    if value != RESULT_OK:
                        raise PicusCommandError(
                            value or "FAILED",
                            f"ENABLE_MOTOR_CONTROL {int(mode)}",
                            enable_no,
                        )
                    return

    def _send_raw(self, data: str, *, timeout: float | None = None) -> str | None:
        ser = self._serial
        if ser is None:
            raise PicusError("pipette is not open")
        no = next(self._counter)
        frame = build_command(no, data)
        deadline = time.monotonic() + (timeout or self._command_timeout)
        response_lines: list[str] = []
        with self._lock:
            try:
                ser.write(frame)
                ser.flush()
            except serial.SerialException as e:
                raise PicusConnectionError(f"write failed: {e}") from e
            while True:
                if time.monotonic() >= deadline:
                    raise PicusError(
                        f"timeout waiting for response to {data!r} (no={no})"
                    )
                try:
                    raw = ser.readline()
                except serial.SerialException as e:
                    raise PicusConnectionError(f"read failed: {e}") from e
                if not raw:
                    continue
                line = raw.decode("ascii", errors="replace")
                kind, value = classify_line(line, no)
                if kind == "result":
                    if value != RESULT_OK:
                        raise PicusCommandError(value or "FAILED", data, no)
                    return (
                        "\n".join(response_lines) if response_lines else None
                    )
                if kind == "response":
                    assert value is not None
                    response_lines.append(value)

    @property
    def port(self) -> str:
        return self._port

    def run_init(self) -> None:
        """Initialize piston (finds home). Call once after power-on."""
        self._send_raw("RUN_INIT")

    def home(self) -> None:
        """Move piston to home position."""
        self._send_raw("HOME")

    def aspirate(self, volume_ul: float, speed: int | None = None) -> None:
        """Aspirate ``volume_ul`` µL at the given speed (1..9)."""
        spd = _clamp_speed(
            speed if speed is not None else self._default_speed
        )
        self._send_raw(f"RUN_ASPIRATE {_vol(volume_ul)} {spd}")

    def dispense(self, volume_ul: float, speed: int | None = None) -> None:
        """Dispense ``volume_ul`` µL at the given speed (1..9)."""
        spd = _clamp_speed(
            speed if speed is not None else self._default_speed
        )
        self._send_raw(f"RUN_DISPENSE {_vol(volume_ul)} {spd}")

    def blow_out(
        self,
        speed: int | None = None,
        *,
        delay_ms: int = 3000,
        go_home: bool = True,
    ) -> None:
        """Run blow-out to expel residual liquid."""
        spd = _clamp_speed(
            speed if speed is not None else self._default_speed
        )
        self._send_raw(
            f"BLOW_OUT {1 if go_home else 0} {spd} {int(delay_ms)}"
        )

    def tip_eject(self) -> None:
        """Eject the mounted tip."""
        self._send_raw("TIP_EJECT")

    def get_serial(self) -> str:
        return self._send_raw("GET_SERIAL", timeout=2.0) or ""

    def get_model(self) -> str:
        return self._send_raw("GET_MODEL", timeout=2.0) or ""

    def get_version(self) -> str:
        return self._send_raw("GET_VERSION", timeout=2.0) or ""

    def get_nominal_volume(self) -> str:
        return self._send_raw("GET_NOMINAL_VOLUME", timeout=2.0) or ""

    def get_battery_level(self) -> str:
        return self._send_raw("GET_BATTERY_LEVEL", timeout=2.0) or ""
