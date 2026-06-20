from datetime import datetime
from zoneinfo import ZoneInfo

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def now() -> datetime:
    return datetime.now(SAO_PAULO_TZ)


def to_sao_paulo(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=SAO_PAULO_TZ)
    return value.astimezone(SAO_PAULO_TZ)


def format_datetime(value: datetime) -> str:
    return to_sao_paulo(value).isoformat(timespec="seconds")
