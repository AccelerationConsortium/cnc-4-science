"""Wire-protocol primitives for the Sartorius Picus 2 pipette."""

from __future__ import annotations

import json

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
    """Classify one received line into (kind, value).

    kind is one of: "envelope", "result", "result_other", "response", "ignore".
    """
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
