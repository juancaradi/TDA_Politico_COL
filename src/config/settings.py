# src/config/settings.py
# ============================================================
# CONFIG GLOBAL — SISMÓGRAFO TDA
# ============================================================
# Nota:
# - Paths se anclan al PROJECT_ROOT para evitar conflictos por cwd.
# - data/ y logs/ ya existen en el repo y se usan como destinos.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# -----------------------------
# PROJECT ROOT (repo root)
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # .../TDA_Politico_COL
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_SAMPLE_DIR = DATA_DIR / "sample"


# -----------------------------
# ZONA HORARIA
# -----------------------------
TZ_LOCAL = ZoneInfo("America/Bogota")
TZ_UTC = timezone.utc


@dataclass(frozen=True)
class Settings:
    # Debug
    DEBUG: bool = True

    # Scraping
    MAX_LOAD_MORE: int = 12
    SLEEP_BETWEEN_PAGES: tuple[float, float] = (2.5, 4.0)
    SLEEP_BETWEEN_MIRRORS: tuple[float, float] = (1.0, 2.0)

    # Subventanas
    SUBWINDOW_MINUTES: int = 10

    # Presupuesto diario por canal
    TOTAL_PER_DAY_PER_CHANNEL_WEEKDAY: int = 2400
    TOTAL_PER_DAY_PER_CHANNEL_WEEKEND: int = 2000

    # Oversample factor
    OVERSAMPLE_FACTOR: int = 3

    # Outputs (en data/logs)
    DATASET_PATH: Path = DATA_PROCESSED_DIR / "SISMOGRAFO_TDA_DATASET.csv"
    WINDOW_LOG_PATH: Path = LOGS_DIR / "window_log.csv"
    REQUEST_LOG_PATH: Path = LOGS_DIR / "request_log.csv"
    RUN_SUMMARY_PATH: Path = LOGS_DIR / "run_summary.json"

    FLUSH_EVERY_N_ROWS: int = 50
    WRITE_HEADER_IF_NEW: bool = True
    REQUEST_LOG_FLUSH_EVERY: int = 25


def ensure_project_dirs() -> None:
    """
    Crea directorios esperados si no existen.
    No crea archivos (solo carpetas).
    """
    for p in [DATA_DIR, LOGS_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_SAMPLE_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def run_start_utc() -> datetime:
    """
    Timestamp de inicio de ejecución (UTC).
    Se calcula una vez en main y se pasa a summary.
    """
    return datetime.now(timezone.utc)
