# src/utils/metrics.py
from __future__ import annotations

import re
from bs4.element import Tag


def clean_metric(txt: str | None) -> int:
    """Convierte '1.2K', '1,2K', '1.1M', '—' a int."""
    if txt is None:
        return 0
    s = txt.strip().upper().replace(",", ".")
    if s in {"", "—", "-", "N/A"}:
        return 0

    m = re.match(r"^\s*([0-9]+(\.[0-9]+)?)\s*([KM])\s*$", s)
    if m:
        num = float(m.group(1))
        mult = 1000 if m.group(3) == "K" else 1_000_000
        return int(num * mult)

    digits = re.findall(r"\d+", s)
    return int("".join(digits)) if digits else 0


def parse_stats_best_effort(item: Tag) -> dict:
    """
    Auditoría:
    - stats_raw (texto original)
    - stats_len
    - stats_suspect (1 si len != 4)
    Asignación típica: [replies, retweets, quotes, likes]
    """
    stats_elems = item.find_all("span", class_="tweet-stat")
    stats_raw = [s.get_text(strip=True) for s in stats_elems]
    stats_clean = [clean_metric(x) for x in stats_raw]

    return {
        "stats_raw": "|".join(stats_raw),
        "stats_len": len(stats_raw),
        "stats_suspect": 0 if len(stats_raw) == 4 else 1,
        "replies": stats_clean[0] if len(stats_clean) > 0 else 0,
        "retweets": stats_clean[1] if len(stats_clean) > 1 else 0,
        "quotes": stats_clean[2] if len(stats_clean) > 2 else 0,
        "likes": stats_clean[3] if len(stats_clean) > 3 else 0,
    }
