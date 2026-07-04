"""Timezone helpers for API timestamps."""
from datetime import datetime, timedelta, timezone

CHINA_TZ = timezone(timedelta(hours=8), "Asia/Shanghai")


def china_now() -> datetime:
    return datetime.now(CHINA_TZ).replace(tzinfo=None)


def china_now_iso() -> str:
    return datetime.now(CHINA_TZ).isoformat(timespec="seconds")


def china_now_text() -> str:
    return datetime.now(CHINA_TZ).strftime("%Y-%m-%d %H:%M:%S")


def format_china_iso(value: datetime | None) -> str:
    if value is None:
        return china_now_iso()

    if value.tzinfo is None:
        value = value.replace(tzinfo=CHINA_TZ)
    else:
        value = value.astimezone(CHINA_TZ)

    return value.isoformat(timespec="seconds")
