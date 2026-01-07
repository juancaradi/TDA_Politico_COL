# src/scraping/extractor.py
# ============================================================
# EXTRAER 1 SUBVENTANA (epoch) — robusto + debug + log
# ============================================================

from __future__ import annotations

import hashlib
import random
import re
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from src.config.settings import Settings, TZ_LOCAL, TZ_UTC
from src.queries.query_core import QUERY_CORE
from src.utils.dates import parse_date_any_utc, to_epoch_utc
from src.utils.metrics import parse_stats_best_effort
from src.utils.text import normalize_whitespace
from src.utils.logging import _short_err, log_window_row, append_csv_rows


def query_hash(q: str) -> str:
    return hashlib.sha1(q.encode("utf-8")).hexdigest()[:12]


def extract_status_id(t_link: str) -> str:
    if not t_link:
        return ""
    m = re.search(r"status/(\d+)", t_link)
    return m.group(1) if m else t_link


def build_search_path_epoch(query_raw: str, sub_start_local, sub_end_local) -> str:
    q = query_raw.replace("\n", " ").strip()
    since_time = to_epoch_utc(sub_start_local)
    until_time = to_epoch_utc(sub_end_local)
    full_query = f"{q} since_time:{since_time} until_time:{until_time}"
    return f"/search?f=tweets&q={urllib.parse.quote(full_query)}"


def extraer_subventana_epoch(
    driver,
    mirrors: list[str],
    settings: Settings,
    telemetry,
    sub_start_local,
    sub_end_local,
    etapa: str,
    target: int,
    window_log_path: Path,
    write_header_if_new: bool,
) -> list[dict]:
    """
    Pide tweets usando since_time/until_time (epoch) para la subventana,
    filtra por dt_tweet convertido a hora local (Bogotá) y recolecta hasta 'target'.
    """
    query_raw = QUERY_CORE[etapa]
    qh = query_hash(query_raw)
    path = build_search_path_epoch(query_raw, sub_start_local, sub_end_local)

    mirrors_local = mirrors[:]
    random.shuffle(mirrors_local)

    need_raw = max(target * settings.OVERSAMPLE_FACTOR, target)

    for mirror in mirrors_local:
        recolectados: list[dict] = []
        ids_vistos: set[str] = set()

        seen_items_total = 0
        dates_ok = 0
        dates_fail = 0
        outside_window = 0
        no_link = 0
        no_content = 0
        pages_used = 0
        stop_reason = "finished_loop"

        t0 = time.time()
        had_error = False
        error_type = ""
        error_msg = ""

        try:
            url = f"{mirror}{path}"
            driver.get(url)
            time.sleep(random.uniform(2.8, 4.2))

            print(
                f"📡 Canal: {etapa} | Mirror: {mirror} | Mode: epoch | Subventana: "
                f"{sub_start_local.strftime('%Y-%m-%d %H:%M')} -> {sub_end_local.strftime('%H:%M')} | "
                f"target={target} | need_raw={need_raw}"
            )

            for page in range(settings.MAX_LOAD_MORE):
                pages_used = page + 1
                time.sleep(random.uniform(*settings.SLEEP_BETWEEN_PAGES))

                soup = BeautifulSoup(driver.page_source, "html.parser")
                items = soup.find_all("div", class_="timeline-item")

                if settings.DEBUG and page == 0:
                    print(f"   🔎 timeline-item encontrados: {len(items)}")
                    if items:
                        first = items[0]
                        print("   🔎 first.tweet-content?", first.find("div", class_="tweet-content") is not None)
                        print("   🔎 first.tweet-link?", first.find("a", class_="tweet-link") is not None)
                        td = first.find("span", class_="tweet-date")
                        print("   🔎 first.tweet-date?", td is not None)
                        if td and td.find("a"):
                            a = td.find("a")
                            print("   🕒 date.title:", a.get("title"))
                            print("   🕒 date.datetime:", a.get("datetime"))
                            print("   🕒 date.href:", a.get("href"))

                for item in items:
                    if len(recolectados) >= target:
                        stop_reason = "meta_reached"
                        break
                    if "show-more" in (item.get("class") or []):
                        continue

                    seen_items_total += 1

                    a_link = item.find("a", class_="tweet-link")
                    if not a_link or not a_link.get("href"):
                        no_link += 1
                        continue

                    t_link = a_link["href"]
                    status_id = extract_status_id(t_link)
                    if not status_id or status_id in ids_vistos:
                        continue
                    ids_vistos.add(status_id)

                    dt_utc = parse_date_any_utc(item)
                    if dt_utc is None:
                        dates_fail += 1
                        continue
                    dates_ok += 1
                    dt_local = dt_utc.astimezone(TZ_LOCAL)

                    if not (sub_start_local <= dt_local < sub_end_local):
                        outside_window += 1
                        continue

                    content = item.find("div", class_="tweet-content")
                    if content is None:
                        no_content += 1
                        continue

                    st = parse_stats_best_effort(item)

                    links = content.find_all("a")
                    hashtags = [x.get_text() for x in links if x.get_text().startswith("#")]
                    mentions = [x.get_text() for x in links if x.get_text().startswith("@")]

                    user_a = item.find("a", class_="username")
                    usuario = user_a.get_text(strip=True) if user_a else ""

                    raw_text = content.get_text(separator=" ", strip=True)
                    norm_text = normalize_whitespace(raw_text)

                    recolectados.append({
                        "window_id": sub_start_local.strftime("%Y-%m-%d %H:%M"),
                        "timestamp_local": dt_local.isoformat(),
                        "timestamp_utc": dt_utc.astimezone(TZ_UTC).isoformat(),
                        "query_type": etapa,
                        "usuario": usuario,
                        "texto_raw": raw_text,
                        "texto_norm": norm_text,
                        "hashtags": "|".join(hashtags),
                        "menciones": "|".join(mentions),
                        "replies": st["replies"],
                        "retweets": st["retweets"],
                        "quotes": st["quotes"],
                        "likes": st["likes"],
                        "stats_raw": st["stats_raw"],
                        "stats_len": st["stats_len"],
                        "stats_suspect": st["stats_suspect"],
                        "status_id": status_id,
                        "mirror_used": mirror,
                        "mode_used": "epoch",
                        "query_hash": qh,
                    })

                    if settings.DEBUG and len(recolectados) <= 2:
                        print(f"   🧪 dt_local={dt_local} | subwindow=[{sub_start_local}, {sub_end_local})")

                if len(recolectados) >= target:
                    break

                try:
                    btn = driver.find_element(By.PARTIAL_LINK_TEXT, "Load more")
                    driver.execute_script("arguments[0].scrollIntoView();", btn)
                    btn.click()
                except Exception:
                    stop_reason = "no_more_pages"
                    break

            # window_log incremental (1 fila por intento mirror+subventana)
            append_csv_rows(
                path=window_log_path,
                rows=[log_window_row(
                    sub_start_local=sub_start_local,
                    sub_end_local=sub_end_local,
                    etapa=etapa,
                    mirror=mirror,
                    mode_used="epoch",
                    requested_target=target,
                    need_raw=need_raw,
                    obtained_n=len(recolectados),
                    pages_used=pages_used,
                    items_seen=seen_items_total,
                    dates_ok=dates_ok,
                    dates_fail=dates_fail,
                    outside_window=outside_window,
                    no_link=no_link,
                    no_content=no_content,
                    stop_reason=stop_reason,
                )],
                write_header_if_new=write_header_if_new,
            )

            if len(recolectados) > 0:
                print(f"   ✅ obtenido {len(recolectados)}/{target} | pages={pages_used} | stop={stop_reason}")
            else:
                if settings.DEBUG:
                    print(
                        f"   🧾 resumen mirror={mirror}: seen={seen_items_total}, dates_ok={dates_ok}, "
                        f"dates_fail={dates_fail}, outside_window={outside_window}, no_link={no_link}, no_content={no_content}"
                    )

        except Exception as e:
            had_error = True
            error_type = type(e).__name__
            error_msg = _short_err(e)

            if settings.DEBUG:
                print(f"   ⚠️ Error en mirror {mirror}: {e}")

            append_csv_rows(
                path=window_log_path,
                rows=[log_window_row(
                    sub_start_local=sub_start_local,
                    sub_end_local=sub_end_local,
                    etapa=etapa,
                    mirror=mirror,
                    mode_used="epoch",
                    requested_target=target,
                    need_raw=need_raw,
                    obtained_n=0,
                    pages_used=0,
                    items_seen=0,
                    dates_ok=0,
                    dates_fail=0,
                    outside_window=0,
                    no_link=0,
                    no_content=0,
                    stop_reason=f"error:{error_type}",
                )],
                write_header_if_new=write_header_if_new,
            )

            time.sleep(random.uniform(*settings.SLEEP_BETWEEN_MIRRORS))

        finally:
            t_total = time.time() - t0
            ok = (len(recolectados) > 0) and (not had_error)

            telemetry.update_after_request(
                channel=etapa,
                mirror=mirror,
                ok=ok,
                obtained=len(recolectados) if not had_error else 0,
                pages_used=pages_used,
                t_total_sec=t_total,
                had_error=had_error,
            )

            telemetry.append_request_log({
                "ts_utc": datetime.utcnow().isoformat(),
                "window_id": sub_start_local.strftime("%Y-%m-%d %H:%M"),
                "window_end": sub_end_local.strftime("%Y-%m-%d %H:%M"),
                "channel": etapa,
                "mirror": mirror,
                "mode_used": "epoch",
                "target": target,
                "need_raw": need_raw,
                "obtained": len(recolectados) if not had_error else 0,
                "pages_used": pages_used,
                "stop_reason": stop_reason if not had_error else f"error:{error_type}",
                "items_seen": seen_items_total,
                "dates_ok": dates_ok,
                "dates_fail": dates_fail,
                "outside_window": outside_window,
                "no_link": no_link,
                "no_content": no_content,
                "t_total_sec": round(t_total, 3),
                "had_error": int(had_error),
                "error_type": error_type,
                "error_msg": error_msg,
            })

        if len(recolectados) > 0:
            time.sleep(random.uniform(*settings.SLEEP_BETWEEN_MIRRORS))
            return recolectados

        time.sleep(random.uniform(*settings.SLEEP_BETWEEN_MIRRORS))

    return []
