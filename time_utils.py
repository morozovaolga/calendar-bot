from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def now_tz(timezone: str) -> datetime:
    """Текущее время в заданной IANA timezone (aware datetime)."""
    return datetime.now(ZoneInfo(timezone))

