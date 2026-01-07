# src/scraping/browser.py
from __future__ import annotations

import undetected_chromedriver as uc


def build_driver(headless: bool = False):
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    if headless:
        options.add_argument("--headless=new")
    driver = uc.Chrome(options=options)
    return driver
