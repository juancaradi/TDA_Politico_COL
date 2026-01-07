# src/utils/logging.py
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

import pandas as pd


def _short_err(e: Exception, maxlen: int = 160) -> str:
    s = str(e).replace("\n", " ").strip()
    return s[:maxlen]


def append_csv_rows(path: Path, rows: list[dict], write_header_if_new: bool = True) -> None:
    """
    Append incremental a CSV (crea header solo si el archivo no existe).
    - Mantiene UTF-8.
    - Evita reescribir todo el dataset/log en memoria.
    """
    if not rows:
        return

    df = pd.DataFrame(rows)
    df.to_csv(
        path,
        mode="a",
        index=False,
        header=(write_header_if_new and (not path.exists())),
        encoding="utf-8",
        lineterminator="\n",
    )


class Heartbeat:
    """
    Heartbeat simple: imprime cada 'every_sec' para confirmar que el proceso sigue vivo.
    """
    def __init__(self, every_sec: float = 30.0):
        self.every_sec = float(every_sec)
        self._last_ts = None

    def tick(self, msg: str = "💓 Heartbeat: running...") -> None:
        now = datetime.now(timezone.utc).timestamp()
        if self._last_ts is None:
            self._last_ts = now
            return
        if (now - self._last_ts) >= self.every_sec:
            print(msg)
            self._last_ts = now


@dataclass
class RunStats:
    total_rows_written: int = 0
    total_tweets_collected: int = 0
    total_requests: int = 0
    requests_ok: int = 0
    requests_empty: int = 0
    requests_error: int = 0
    total_pages: int = 0

    by_channel: dict = field(default_factory=lambda: defaultdict(lambda: {"tweets": 0, "requests": 0, "ok": 0, "empty": 0, "error": 0}))
    by_mirror: dict = field(default_factory=lambda: defaultdict(lambda: {"tweets": 0, "requests": 0, "ok": 0, "empty": 0, "error": 0, "lat_sum": 0.0}))


class Telemetry:
    def __init__(self, request_log_path: Path, run_summary_path: Path, write_header_if_new: bool, request_log_flush_every: int):
        self.request_log_path = request_log_path
        self.run_summary_path = run_summary_path
        self.write_header_if_new = write_header_if_new
        self.request_log_flush_every = request_log_flush_every

        self.run_start_utc = datetime.now(timezone.utc)
        self.stats = RunStats()
        self._request_log_buffer: list[dict] = []

    def append_request_log(self, row: dict) -> None:
        self._request_log_buffer.append(row)
        if len(self._request_log_buffer) >= self.request_log_flush_every:
            self.flush_request_log()

    def flush_request_log(self) -> None:
        if not self._request_log_buffer:
            return
        append_csv_rows(
            path=self.request_log_path,
            rows=self._request_log_buffer,
            write_header_if_new=self.write_header_if_new,
        )
        self._request_log_buffer = []

    def update_after_request(self, channel: str, mirror: str, ok: bool, obtained: int, pages_used: int, t_total_sec: float, had_error: bool) -> None:
        s = self.stats
        s.total_requests += 1
        s.total_pages += int(pages_used)

        s.by_channel[channel]["requests"] += 1
        s.by_mirror[mirror]["requests"] += 1
        s.by_mirror[mirror]["lat_sum"] += float(t_total_sec)

        if had_error:
            s.requests_error += 1
            s.by_channel[channel]["error"] += 1
            s.by_mirror[mirror]["error"] += 1
            return

        if ok:
            s.requests_ok += 1
            s.by_channel[channel]["ok"] += 1
            s.by_mirror[mirror]["ok"] += 1
        else:
            s.requests_empty += 1
            s.by_channel[channel]["empty"] += 1
            s.by_mirror[mirror]["empty"] += 1

        s.total_tweets_collected += int(obtained)
        s.by_channel[channel]["tweets"] += int(obtained)
        s.by_mirror[mirror]["tweets"] += int(obtained)

    def add_rows_written(self, n: int) -> None:
        self.stats.total_rows_written += int(n)

    def write_run_summary(self, dataset_path: Path, window_log_path: Path) -> None:
        end_utc = datetime.now(timezone.utc)
        elapsed = (end_utc - self.run_start_utc).total_seconds()

        by_channel = {k: dict(v) for k, v in self.stats.by_channel.items()}
        by_mirror = {}
        for k, v in self.stats.by_mirror.items():
            vv = dict(v)
            vv["avg_latency_sec"] = (vv["lat_sum"] / vv["requests"]) if vv["requests"] else None
            by_mirror[k] = vv

        summary = {
            "run_start_utc": self.run_start_utc.isoformat(),
            "run_end_utc": end_utc.isoformat(),
            "elapsed_sec": elapsed,
            "dataset_path": str(dataset_path),
            "window_log_path": str(window_log_path),
            "request_log_path": str(self.request_log_path),
            "total_tweets_collected": self.stats.total_tweets_collected,
            "total_rows_written": self.stats.total_rows_written,
            "total_requests": self.stats.total_requests,
            "requests_ok": self.stats.requests_ok,
            "requests_empty": self.stats.requests_empty,
            "requests_error": self.stats.requests_error,
            "total_pages": self.stats.total_pages,
            "throughput_tweets_per_min": (self.stats.total_tweets_collected / elapsed) * 60 if elapsed > 0 else 0,
            "by_channel": by_channel,
            "by_mirror": by_mirror,
        }

        with open(self.run_summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)


def print_block_dashboard(sub_start_local: datetime, sub_end_local: datetime, channel: str,
                          target: int, obtained: int, attempts: int, ok_requests: int, elapsed_sec: float) -> None:
    rpm = (obtained / elapsed_sec) * 60 if elapsed_sec > 0 else 0
    ok_rate = (ok_requests / attempts) * 100 if attempts > 0 else 0
    sid = f"{sub_start_local.strftime('%Y-%m-%d %H:%M')}->{sub_end_local.strftime('%H:%M')}"
    print(f"📊 BLOQUE {sid} | {channel} | target={target} obtained={obtained} | "
          f"req={attempts} ok%={ok_rate:.1f}% | speed={rpm:.1f} tweets/min | dt={elapsed_sec:.1f}s")


def log_window_row(sub_start_local, sub_end_local, etapa, mirror, mode_used,
                   requested_target, need_raw, obtained_n, pages_used,
                   items_seen, dates_ok, dates_fail, outside_window,
                   no_link, no_content, stop_reason) -> dict:
    total_dates = dates_ok + dates_fail
    fail_rate = (dates_fail / total_dates) if total_dates > 0 else None

    return {
        "window_id": sub_start_local.strftime("%Y-%m-%d %H:%M"),
        "window_end": sub_end_local.strftime("%Y-%m-%d %H:%M"),
        "query_type": etapa,
        "mirror_used": mirror,
        "mode_used": mode_used,
        "requested_target": requested_target,
        "need_raw": need_raw,
        "obtained_n": obtained_n,
        "pages_used": pages_used,
        "items_seen": items_seen,
        "dates_ok": dates_ok,
        "dates_fail": dates_fail,
        "date_fail_rate": fail_rate,
        "outside_window": outside_window,
        "no_link": no_link,
        "no_content": no_content,
        "stop_reason": stop_reason,
    }
