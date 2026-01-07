# src/utils/dates.py
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import timezone

TZ_UTC = timezone.utc


def parse_date_title_utc(title: str) -> datetime | None:
    """
    title: 'Jun 4, 2025 · 11:59 PM UTC'
    Devuelve datetime aware en UTC.
    """
    try:
        p = title.split("·")
        d = p[0].strip()
        t = p[1].strip().replace(" UTC", "")
        dt_naive = datetime.strptime(f"{d} {t}", "%b %d, %Y %I:%M %p")
        return dt_naive.replace(tzinfo=TZ_UTC)
    except Exception:
        return None


def parse_date_any_utc(item) -> datetime | None:
    """
    Intenta extraer fecha/hora del tweet como datetime aware UTC.
    Prioriza el atributo title que contiene hora exacta + 'UTC'.
    """
    td = item.find("span", class_="tweet-date")
    if not td:
        return None
    a = td.find("a")
    if not a:
        return None

    title = a.get("title")
    if title:
        dt = parse_date_title_utc(title)
        if dt:
            return dt

    dt_iso = a.get("datetime")
    if dt_iso:
        try:
            return datetime.fromisoformat(dt_iso.replace("Z", "+00:00")).astimezone(TZ_UTC)
        except Exception:
            return None

    return None


def to_epoch_utc(dt_local_aware: datetime) -> int:
    """Convierte un datetime aware en TZ_LOCAL a epoch UTC (segundos)."""
    return int(dt_local_aware.astimezone(TZ_UTC).timestamp())
