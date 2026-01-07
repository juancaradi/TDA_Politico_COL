# src/scraping/orchestrator.py
# ============================================================
# ORQUESTADOR: por día -> por hora -> por subventana 10 min
# ============================================================

from __future__ import annotations

import random
import time
from datetime import datetime, timedelta

import pandas as pd

from src.config.settings import Settings, TZ_LOCAL
from src.queries.query_core import CHANNELS
from src.utils.logging import print_block_dashboard
from src.scraping.extractor import extraer_subventana_epoch


def is_weekend_local(d: datetime) -> bool:
    return d.weekday() >= 5


def hourly_traffic_profile(is_weekend: bool) -> list[float]:
    if not is_weekend:
        return [
            0.35, 0.30, 0.28, 0.25, 0.28, 0.40, 0.70, 0.95,
            1.15, 1.30, 1.45, 1.55, 1.60, 1.55, 1.50, 1.45,
            1.35, 1.25, 1.10, 0.95, 0.80, 0.65, 0.50, 0.40
        ]
    return [
        0.30, 0.28, 0.26, 0.24, 0.26, 0.35, 0.55, 0.75,
        0.95, 1.10, 1.20, 1.30, 1.40, 1.45, 1.50, 1.55,
        1.50, 1.40, 1.25, 1.10, 0.95, 0.80, 0.55, 0.40
    ]


def subwindow_profile_within_hour() -> list[float]:
    return [1.05, 1.10, 1.15, 1.10, 0.95, 0.85]


def allocate_targets_for_hour(hour_target: int) -> list[int]:
    w = subwindow_profile_within_hour()
    s = sum(w)
    raw = [hour_target * (x / s) for x in w]
    targets = [int(round(x)) for x in raw]

    diff = hour_target - sum(targets)
    i = 0
    while diff != 0 and i < 1000:
        idx = i % len(targets)
        if diff > 0:
            targets[idx] += 1
            diff -= 1
        else:
            if targets[idx] > 0:
                targets[idx] -= 1
                diff += 1
        i += 1
    return targets


def allocate_targets_for_day_by_hour(total_per_day: int, is_weekend: bool) -> list[int]:
    w = hourly_traffic_profile(is_weekend)
    s = sum(w)
    raw = [total_per_day * (x / s) for x in w]
    targets = [int(round(x)) for x in raw]

    diff = total_per_day - sum(targets)
    i = 0
    while diff != 0 and i < 5000:
        idx = i % 24
        if diff > 0:
            targets[idx] += 1
            diff -= 1
        else:
            if targets[idx] > 0:
                targets[idx] -= 1
                diff += 1
        i += 1
    return targets


def allocate_targets_for_day(total_per_day: int):
    """
    Placeholder (si luego quieres retornar dict {hour: target}).
    Lo dejamos por compatibilidad conceptual con tu script original.
    """
    return None


class IncrementalWriter:
    def __init__(self, dataset_path, flush_every: int, write_header_if_new: bool, telemetry):
        self.dataset_path = dataset_path
        self.flush_every = flush_every
        self.write_header_if_new = write_header_if_new
        self.telemetry = telemetry
        self.buffer: list[dict] = []

    def append_rows(self, rows: list[dict]) -> None:
        self.buffer.extend(rows)
        if len(self.buffer) >= self.flush_every:
            self.flush()

    def flush(self) -> None:
        if not self.buffer:
            return
        df = pd.DataFrame(self.buffer)
        df.to_csv(
            self.dataset_path,
            mode="a",
            index=False,
            header=(self.write_header_if_new and (not self.dataset_path.exists())),
        )
        self.telemetry.add_rows_written(len(self.buffer))
        print(f"💾 Flush dataset: +{len(self.buffer)} filas -> {self.dataset_path}")
        self.buffer = []


def run_study(driver, mirrors: list[str], settings: Settings, telemetry,
              start_study: datetime, end_study: datetime) -> tuple[list[dict], IncrementalWriter]:
    window_log: list[dict] = []
    writer = IncrementalWriter(
        dataset_path=settings.DATASET_PATH,
        flush_every=settings.FLUSH_EVERY_N_ROWS,
        write_header_if_new=settings.WRITE_HEADER_IF_NEW,
        telemetry=telemetry,
    )

    day_cursor = start_study
    while day_cursor < end_study:
        day_start = day_cursor.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        if day_end > end_study:
            day_end = end_study

        weekend = is_weekend_local(day_start)
        total_per_day = settings.TOTAL_PER_DAY_PER_CHANNEL_WEEKEND if weekend else settings.TOTAL_PER_DAY_PER_CHANNEL_WEEKDAY
        hour_targets = allocate_targets_for_day_by_hour(total_per_day, is_weekend=weekend)

        print("\n" + "#" * 94)
        print(f"📅 DÍA LOCAL: {day_start.strftime('%Y-%m-%d')} | weekend={weekend} | total_per_day_per_channel={total_per_day}")
        print("#" * 94)

        hour_cursor = day_start
        while hour_cursor < day_end:
            hour_end = hour_cursor + timedelta(hours=1)

            hour_idx = hour_cursor.hour
            hour_target = hour_targets[hour_idx]
            sub_targets = allocate_targets_for_hour(hour_target)

            if hour_target == 0:
                if settings.DEBUG:
                    print(f"⏩ Hora {hour_cursor.strftime('%H:00')} target=0 (saltando)")
                hour_cursor = hour_end
                continue

            print("\n" + "=" * 78)
            print(f"🕒 Hora local: {hour_cursor.strftime('%Y-%m-%d %H:00')} -> {hour_end.strftime('%H:00')} | hour_target={hour_target}")
            print("=" * 78)

            for etapa in CHANNELS:
                print("\n" + "-" * 86)
                print(f"📌 CANAL: {etapa} | objetivo hora={hour_target} | subtargets={sub_targets}")
                print("-" * 86)

                for i in range(6):
                    sub_start = hour_cursor + timedelta(minutes=i * settings.SUBWINDOW_MINUTES)
                    sub_end = sub_start + timedelta(minutes=settings.SUBWINDOW_MINUTES)
                    target = sub_targets[i]

                    if target <= 0:
                        if settings.DEBUG:
                            print(f"⏩ Subventana {sub_start.strftime('%H:%M')}->{sub_end.strftime('%H:%M')} target=0 (skip)")
                        continue

                    print("\n" + "-" * 86)
                    print(f"⏱️  Subventana {sub_start.strftime('%Y-%m-%d %H:%M')} -> {sub_end.strftime('%H:%M')} | {etapa} | target={target}")
                    print("-" * 86)

                    block_t0 = time.time()

                    lote = extraer_subventana_epoch(
                        driver=driver,
                        mirrors=mirrors,
                        settings=settings,
                        telemetry=telemetry,
                        sub_start_local=sub_start,
                        sub_end_local=sub_end,
                        etapa=etapa,
                        target=target,
                        window_log=window_log,
                    )

                    attempts = 1
                    ok_requests = 1 if lote else 0
                    obtained_total = len(lote) if lote else 0

                    if lote:
                        writer.append_rows(lote)
                        print(f"   ✅ Append+flush OK | +{len(lote)} rows | buffer={len(writer.buffer)}")
                    else:
                        print("   ⚠️  Subventana sin datos (ningún mirror entregó tweets válidos).")

                    block_dt = time.time() - block_t0
                    print_block_dashboard(sub_start, sub_end, etapa, target, obtained_total, attempts, ok_requests, block_dt)

                    time.sleep(random.uniform(0.8, 1.6))

            hour_cursor = hour_end

        day_cursor = day_start + timedelta(days=1)

    return window_log, writer
