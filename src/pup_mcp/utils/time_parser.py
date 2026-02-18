"""Time string parsing utilities mirroring pup CLI's relative time support."""

import re
import time
from datetime import datetime

from pup_mcp.exceptions import TimeParseError

_RELATIVE_RE = re.compile(r"^(\d+)([smhdw])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_time(value: str) -> int:
    """Parse a time string to Unix epoch seconds.

    Supports three formats:
      - Relative: ``1h``, ``30m``, ``7d``, ``1w`` (subtracted from now)
      - Absolute Unix timestamp: ``1700000000``
      - ISO 8601 / RFC 3339: ``2024-01-15T10:30:00Z``

    Args:
        value: The time string to parse.

    Returns:
        Unix epoch seconds as an integer.

    Raises:
        TimeParseError: If the string does not match any supported format.
    """
    # Unix timestamp (10+ digits)
    if re.match(r"^\d{10,}$", value):
        return int(value)

    # Relative offset
    match = _RELATIVE_RE.match(value)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return int(time.time()) - amount * _UNIT_SECONDS[unit]

    # ISO 8601 / RFC 3339
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except (ValueError, TypeError):
        pass

    raise TimeParseError(
        f"Invalid time: '{value}'. "
        "Use relative (1h, 30m, 7d), Unix timestamp, or RFC 3339."
    )


def parse_time_range(from_time: str, to_time: str | None) -> tuple[int, int]:
    """Parse a from/to time pair into Unix epoch seconds.

    Args:
        from_time: Start time (relative, absolute, or ISO 8601).
        to_time: End time, or ``None`` to default to now.

    Returns:
        A (from_ts, to_ts) tuple of Unix epoch seconds.
    """
    from_ts = parse_time(from_time)
    to_ts = parse_time(to_time) if to_time else now_unix()
    return from_ts, to_ts


def now_unix() -> int:
    """Return the current time as Unix epoch seconds."""
    return int(time.time())
