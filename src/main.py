# src/main.py
# ============================================================
# SISMÓGRAFO TDA (Nitter/XCancel mirrors) — COMPLETO + DEBUG
# ============================================================
# ✅ Ventanas reales (subventanas) con since_time/until_time (epoch)
# ✅ FIX CRÍTICO: manejo correcto de zona horaria (Bogotá vs UTC)
# ✅ Deduplicación robusta por status_id (entre mirrors y dentro de ventana)
# ✅ Métricas K/M robustas + auditoría stats_raw
# ✅ Hashtags + menciones
# ✅ Canal MEDIOS separado (TIPO_B2_MEDIOS)
# ✅ window_log.csv (auditoría por subventana/canal/mirror)
# ✅ Debug en consola (conteos, fechas, razón de descarte)
# ✅ Guardado incremental (flush) sin cargar todo en RAM
# ✅ Limpieza de texto con “mojibake fix” (CagÃ© -> Cagué), best-effort
#
# ✅ (AGREGADO) request_log.csv: 1 fila por intento (mirror+subventana)
# ✅ (AGREGADO) run_summary.json: resumen final (volumen, tasas, latencia, fallos)
# ✅ (AGREGADO) Dashboard en consola por subventana: reqs, ok%, tweets/min, elapsed
# ✅ (AGREGADO) Métricas de desempeño por canal y por mirror (telemetría ligera)
#
# Nota:
# - Mirrors pueden variar; usamos fallback espejo a espejo.
# - El orden es “más reciente primero”; mitigamos sesgo usando subventanas pequeñas
#   y presupuesto proporcional (prior) por hora/minuto.
# ============================================================

from __future__ import annotations

from datetime import datetime, timedelta
import pandas as pd

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

    window_log = []
    writer = None

    try:
        window_log, writer = run_study(
            driver=driver,
            mirrors=MIRRORS,
            settings=settings,
            telemetry=telemetry,
            start_study=start_study,
            end_study=end_study,
        )

    finally:
        # Flush final dataset buffer
        if writer is not None:
            writer.flush()

        # Flush final request_log
        telemetry.flush_request_log()

        # Guardar window_log completo
        if window_log:
            pd.DataFrame(window_log).to_csv(settings.WINDOW_LOG_PATH, index=False)
            print(f"🧾 window_log guardado en: {settings.WINDOW_LOG_PATH}")

        # run_summary final
        telemetry.write_run_summary(
            dataset_path=settings.DATASET_PATH,
            window_log_path=settings.WINDOW_LOG_PATH,
        )
        print(f"✅ run_summary.json guardado en: {settings.RUN_SUMMARY_PATH}")
        print(f"✅ request_log.csv guardado en: {settings.REQUEST_LOG_PATH}")

        driver.quit()

        print("\n✅ Proceso finalizado.")
        print(f"   - Dataset:      {settings.DATASET_PATH}")
        print(f"   - window_log:   {settings.WINDOW_LOG_PATH}")
        print(f"   - request_log:  {settings.REQUEST_LOG_PATH}")
        print(f"   - run_summary:  {settings.RUN_SUMMARY_PATH}")
        print("   Tip rápido de diagnóstico con window_log:")
        print("     - outside_window alto => TZ mal (pero aquí ya está corregido con Bogota<->UTC)")
        print("     - dates_fail alto     => cambió HTML/selector del date.title")
        print("     - obtained_n bajo     => poca densidad o necesitas más mirrors / más Load more")


if __name__ == "__main__":
    main()
