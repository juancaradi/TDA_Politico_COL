# src/main.py
# ============================================================
# SISMÓGRAFO TDA (Nitter/XCancel mirrors) — COMPLETO + DEBUG
# ============================================================

from __future__ import annotations

from datetime import datetime

from src.config.settings import Settings, TZ_LOCAL, ensure_project_dirs
from src.queries.mirrors import MIRRORS
from src.scraping.browser import build_driver
from src.scraping.orchestrator import run_study
from src.utils.logging import Telemetry


def main() -> None:
    settings = Settings()

    ensure_project_dirs()

    telemetry = Telemetry(
        request_log_path=settings.REQUEST_LOG_PATH,
        run_summary_path=settings.RUN_SUMMARY_PATH,
        write_header_if_new=settings.WRITE_HEADER_IF_NEW,
        request_log_flush_every=settings.REQUEST_LOG_FLUSH_EVERY,
    )

    driver = build_driver(headless=False)

    # --- RANGO DEL ESTUDIO (LOCAL Bogotá) ---
    # Pre y Post: 4 Jun 2025 00:00 hasta 11 Jun 2025 00:00 (Bogotá)
    start_study = datetime(2025, 6, 4, 0, 0, tzinfo=TZ_LOCAL)
    end_study = datetime(2025, 6, 11, 0, 0, tzinfo=TZ_LOCAL)

    writer = None
    stopped_by_keyboard = False

    try:
        writer = run_study(
            driver=driver,
            mirrors=MIRRORS,
            settings=settings,
            telemetry=telemetry,
            start_study=start_study,
            end_study=end_study,
        )

    except KeyboardInterrupt:
        stopped_by_keyboard = True
        print("\n🛑 Detenido manualmente por teclado (Ctrl + C). Guardando progreso y cerrando...")

    finally:
        # Flush final dataset buffer
        if writer is not None:
            writer.flush()

        # Flush final request_log
        telemetry.flush_request_log()

        # run_summary final
        telemetry.write_run_summary(
            dataset_path=settings.DATASET_PATH,
            window_log_path=settings.WINDOW_LOG_PATH,
        )

        print(f"✅ run_summary.json guardado en: {settings.RUN_SUMMARY_PATH}")
        print(f"✅ request_log.csv guardado en: {settings.REQUEST_LOG_PATH}")
        print(f"✅ window_log.csv guardado en:  {settings.WINDOW_LOG_PATH}")

        try:
            driver.quit()
        except Exception:
            pass

        if stopped_by_keyboard:
            print("✅ Cierre limpio tras Ctrl + C (sin errores).")

        print("\n✅ Proceso finalizado.")
        print(f"   - Dataset RAW:  {settings.DATASET_PATH}")
        print(f"   - window_log:   {settings.WINDOW_LOG_PATH}")
        print(f"   - request_log:  {settings.REQUEST_LOG_PATH}")
        print(f"   - run_summary:  {settings.RUN_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
